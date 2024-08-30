import csv
from fastapi import APIRouter, status, Body, Request, Form, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from typing import Optional
from io import StringIO

from .models import CSVupload, Product, ProductInDB
from utils.enums import ProcessingStatusEnum
from utils.motor_utilities import (
    get_collection,
    create_document,
    read_collection,
    read_document,
    update_document
)
from utils.helpers import process_product

router = APIRouter()

# ----------------- Upload CSV -----------------
@router.post("/upload", response_description="Upload CSV")
async def upload_csv(request: Request,
                     background_tasks: BackgroundTasks,
                     csv_file: UploadFile = File(...),
                     webhook_url: Optional[str] = Form(None)):
    try:
        csv_upload = CSVupload()
        csv_upload_doc = await create_document("csv_uploads", jsonable_encoder(csv_upload))
        csv_upload_id = csv_upload_doc['_id']

        contents = await csv_file.read()
        csv_content = contents.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_content))

        for row in csv_reader:
            product = Product(
                name=row["Product Name"],
                input_image_urls=row["Input Image URLs"].split(',')
            )

            product_in_db = ProductInDB(**product.dict(), associated_csv=csv_upload)
            product_doc = await create_document("products", jsonable_encoder(product_in_db))

            background_tasks.add_task(process_product, str(product_doc['_id']), webhook_url)

        return {"message": "CSV uploaded successfully", "csv_upload_id": str(csv_upload_id)}

    except Exception as e:
        await update_document("csv_uploads", csv_upload_id, {"status": ProcessingStatusEnum.FAILED})
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- Status -----------------
@router.get("/status/{csv_upload_id}", response_description="Get CSV Processing status")
async def get_status(csv_upload_id: str):
    csv_upload = await read_document("csv_uploads", csv_upload_id)
    return {"status": csv_upload["status"]}


# ----------------- Download new csv -----------------
@router.get("/download/{csv_upload_id}", response_description="Download new CSV")
async def download_csv(csv_upload_id: str):
    csv_upload = await read_document("csv_uploads", csv_upload_id)
    if not csv_upload:
        raise HTTPException(status_code=404, detail="CSV upload not found")

    products = await read_collection("products", {"associated_csv._id": csv_upload_id})

    csv_file = StringIO()
    fieldnames = ["S. No.", "Product Name", "Input Image URLs", "Output Image URLs"]
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    for i, product in enumerate(products["documents"], start=1):
        csv_writer.writerow({
            "S. No.": i,
            "Product Name": product["name"],
            "Input Image URLs": "\n".join(product["input_image_urls"]),
            "Output Image URLs": "\n".join(product.get("output_image_urls", []))
        })

    csv_file.seek(0)

    return StreamingResponse(
        iter([csv_file.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={csv_upload_id}.csv"
        }
    )

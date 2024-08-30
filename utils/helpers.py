from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
from utils.enums import ProcessingStatusEnum
from utils.motor_utilities import (
    read_document,
    update_document
)
import aiohttp
from PIL import Image
from io import BytesIO
import os

async def compress_image_from_url(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))

                    # Resize image to 50%
                    width, height = image.size
                    new_size = (width // 2, height // 2)
                    compressed_image = image.resize(new_size, Image.Resampling.LANCZOS)

                    compressed_image_io = BytesIO()
                    compressed_image.save(compressed_image_io, format=image.format)
                    compressed_image_io.seek(0)
                    return compressed_image_io
                else:
                    return None
    except:
        return None


async def process_product(product_id: str, webhook_url: str = None):
    product = await read_document("products", product_id)
    input_image_urls = product.get("input_image_urls")
    output_image_urls = []
    required_fields = [
        "type", "project_id", "private_key_id", "private_key", "client_email",
        "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url",
        "client_x509_cert_url"
    ]
    credentials_dict = {}
    for field in required_fields:
        value = os.environ.get(field)
        if not value:
            raise ValueError(f"Missing required environment variable: {field}")
        if field == "private_key":
            value = value.replace("\\n", "\n")
        credentials_dict[field] = value

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        credentials_dict
    )
    print("Credentials loaded successfully")

    for url in input_image_urls:
        compressed_image = await compress_image_from_url(url)
        if not compressed_image:
            continue

        # Upload the compressed image to Google Cloud Storage
        storage_client = storage.Client(credentials=credentials, project="csv-parser")
        bucket = storage_client.bucket("images_compressed")
        blob = bucket.blob(f"{product_id}_{url.split('/')[-1]}")
        blob.upload_from_file(compressed_image, content_type="image/jpeg", size=compressed_image.getbuffer().nbytes)

        output_image_urls.append(blob.public_url)

    await update_document("products", product_id, {"output_image_urls": output_image_urls})

    csv_id = product.get("associated_csv")["_id"]
    await update_document("csv_uploads", csv_id, {"status": ProcessingStatusEnum.SUCCESS})

    if webhook_url:
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"product_id": product_id, "status": ProcessingStatusEnum.SUCCESS})
    return True
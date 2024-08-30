from fastapi import HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request

from config import settings

client = AsyncIOMotorClient(settings.DB_URL)
db = client[settings.DB_NAME]


async def get_collection(collection_name: str):
    collection = db.get_collection(collection_name)
    return collection


async def read_collection(collection_name: str, query: dict = None, skip: int = 0, limit: int = 2):
    collection = await get_collection(collection_name)
    documents = []
    total_count = await collection.count_documents(query or {})

    if query:
        cursor = collection.find(query).skip(skip).limit(limit)
        async for document in cursor:
            documents.append(document)
    else:
        cursor = collection.find().skip(skip).limit(limit)
        async for document in cursor:
            documents.append(document)

    has_next = (skip + len(documents)) < total_count
    has_previous = skip > 0

    return {
        "count": len(documents),
        "total_count": total_count,
        "has_next": has_next,
        "has_previous": has_previous,
        "documents": documents,
    }


async def read_document(collection_name: str, id: str):
    collection = await get_collection(collection_name)
    document = await collection.find_one({"_id": id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


async def create_document(collection_name: str, data):
    collection = await get_collection(collection_name)
    document = await collection.insert_one(data)
    inserted_document = await collection.find_one({"_id": document.inserted_id})
    return inserted_document

async def update_document(collection_name: str, id: str, data):
    collection = await get_collection(collection_name)
    doc = await collection.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await collection.update_one({"_id": id}, {"$set": data})
    updated_doc = await collection.find_one({"_id": id})
    return updated_doc
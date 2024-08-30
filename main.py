from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

import uuid

import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

from parser.routers import router as parser_routers

app = FastAPI()
client = AsyncIOMotorClient(settings.DB_URL)
db = client[settings.DB_NAME]

origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_NAME]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def test():
    return {"message": "Hello World"}

app.include_router(parser_routers, prefix="/api/v1", tags=["parser"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        reload=settings.DEBUG_MODE,
        port=settings.SERVER_PORT,
    )
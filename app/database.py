# app/database.py

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "inboxai")

client = AsyncIOMotorClient(
    MONGO_URI,
    maxPoolSize=10,
    minPoolSize=2,
    serverSelectionTimeoutMS=5000,
)

db = client[DB_NAME]

users_collection = db["users"]
accounts_collection = db["accounts"]
threads_collection = db["threads"]
drafts_collection = db["drafts"]
activity_collection = db["activity"]
drafts_collection = db["drafts"]
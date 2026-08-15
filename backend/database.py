"""Single source of truth for the MongoDB connection.

Kept intentionally tiny so every module shares one client/pool. All persistence
flows through `db`; no other file constructs a Mongo client.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

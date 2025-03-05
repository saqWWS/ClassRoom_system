from motor.motor_asyncio import AsyncIOMotorClient

from app.config.settings import settings

client = AsyncIOMotorClient(settings.MONGODB)

db = client["classroom"]
collection_users = db["users"]
collection_schedules = db["schedules"]

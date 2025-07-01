from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# MongoDB connection
MONGODB_CONNECTION_STRING = settings.MONGODB_CONNECTION_STRING
DATABASE_NAME = settings.DATABASE_NAME

# Global client instance
client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    """Create database connection"""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
        # Actually test the connection by running a command
        await client.admin.command('ping')
        db = client[DATABASE_NAME]
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

async def get_database():
    """Get database instance"""
    return db

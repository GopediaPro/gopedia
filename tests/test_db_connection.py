import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
sys.path.append(os.getcwd())

from src.core.config import settings

async def test_connection():
    print(f"Testing connection to: {settings.DATABASE_URL}")
    try:
        # Create async engine
        engine = create_async_engine(str(settings.DATABASE_URL))
        
        # Try to connect and execute simple query
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            print(f"Query 'SELECT 1' returned: {val}")
            assert val == 1
            
        await engine.dispose()
        print("Database connection successful!")
        
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())

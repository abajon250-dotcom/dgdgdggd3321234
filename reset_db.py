import asyncio
import asyncpg
import os

async def reset():
    # Берём DATABASE_URL из переменных окружения
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    conn = await asyncpg.connect(db_url)
    await conn.execute("DROP SCHEMA public CASCADE;")
    await conn.execute("CREATE SCHEMA public;")
    await conn.close()
    print("Schema reset successfully")

if __name__ == "__main__":
    asyncio.run(reset())
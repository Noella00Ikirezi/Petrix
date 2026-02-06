#!/usr/bin/env python3
"""Script to add 'directive' value to PostgreSQL documenttype enum."""

import asyncio
import os

import asyncpg

async def add_directive_to_enum():
    """Add 'directive' to the documenttype enum in PostgreSQL."""

    # Connection via DATABASE_URL or individual env vars
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        conn = await asyncpg.connect(database_url)
    else:
        conn = await asyncpg.connect(
            user=os.environ.get('POSTGRES_USER', 'grc'),
            password=os.environ.get('POSTGRES_PASSWORD', ''),
            database=os.environ.get('POSTGRES_DB', 'grc_platform'),
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=int(os.environ.get('POSTGRES_PORT', '5432'))
        )

    try:
        # Check if 'directive' already exists in the enum
        result = await conn.fetch("""
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documenttype')
        """)

        existing_values = [row['enumlabel'] for row in result]
        print(f"Current enum values: {existing_values}")

        if 'directive' in existing_values:
            print("✓ 'directive' already exists in documenttype enum")
        else:
            # Add the new value
            await conn.execute("ALTER TYPE documenttype ADD VALUE 'directive'")
            print("✓ Added 'directive' to documenttype enum")

            # Verify
            result = await conn.fetch("""
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'documenttype')
            """)
            print(f"Updated enum values: {[row['enumlabel'] for row in result]}")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_directive_to_enum())

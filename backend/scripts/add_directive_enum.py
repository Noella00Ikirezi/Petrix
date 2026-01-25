#!/usr/bin/env python3
"""Script to add 'directive' value to PostgreSQL documenttype enum."""

import asyncio
import asyncpg

async def add_directive_to_enum():
    """Add 'directive' to the documenttype enum in PostgreSQL."""

    # Connection parameters - adjust as needed
    conn = await asyncpg.connect(
        user='grc',
        password='REMOVED_SECRET',
        database='grc_platform',
        host='localhost',
        port=5432
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

"""Promote a registered user to the admin role.

There's no API endpoint for this deliberately — a self-serve "become
admin" route would be a real privilege-escalation hole. This is the
out-of-band path an operator runs against the real database.

Usage (from the backend/ directory, with the venv active):
    python scripts/promote_admin.py owner@example.com
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database.mongodb import connect_to_mongo, close_mongo_connection, get_database  # noqa: E402
from app.database.utils import find_one  # noqa: E402


async def main(email: str) -> None:
    await connect_to_mongo()
    try:
        db = get_database()
        user = await find_one(db["users"], {"email": email.lower()})
        if user is None:
            print(f"No user found with email: {email}")
            return
        await db["users"].update_one({"email": email.lower()}, {"$set": {"role": "admin"}})
        print(f"{email} is now an admin.")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote a user to admin")
    parser.add_argument("email")
    args = parser.parse_args()
    asyncio.run(main(args.email))

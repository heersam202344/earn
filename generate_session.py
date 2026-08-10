"""
Telethon String Session Generator
Run this ONCE on your local machine to get STRING_SESSION
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=" * 60)
print("PAGAL Escrow Bot - String Session Generator")
print("=" * 60)
print()

API_ID = int(input("Enter your API_ID: "))
API_HASH = input("Enter your API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    session_string = client.session.save()
    print()
    print("✅ YOUR STRING SESSION:")
    print("-" * 60)
    print(session_string)
    print("-" * 60)
    print()
    print("Copy this and save it as STRING_SESSION in Railway!")

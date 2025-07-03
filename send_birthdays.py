import os
import asyncio
from datetime import datetime
import pandas as pd
from telethon import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from dotenv import load_dotenv

# 1) Load environment variables
load_dotenv()
API_ID   = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_NAME = 'autoresponder_session'  # will store in 'autoresponder_session.session'


async def main():
    # 2) Authenticate (uses saved session or prompts OTP on first run)
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    # 3) Read the Excel sheet and ensure phone is string
    df = pd.read_excel('birthdays.xlsx', engine='openpyxl', parse_dates=['birthday'])
    df['phone'] = df['phone'].astype(str).apply(lambda x: x if x.startswith('+') else '+' + x)

    # 4) Filter for today’s birthdays
    today = datetime.today()
    df_today = df[
        (df['birthday'].dt.month == today.month) &
        (df['birthday'].dt.day   == today.day)
    ]

    if df_today.empty:
        print('No birthdays today.')
        await client.disconnect()
        return

    # 5) Loop through each birthday row
    for _, row in df_today.iterrows():
        phone      = row['phone']        # E.164 format string
        first_name = row['first_name']   # e.g. 'Aditya'
        other_name = row['other_name']   # e.g. 'Yadav'

        # 6) Import as a contact so Telethon can resolve the entity
        contact = InputPhoneContact(
            client_id=0,
            phone=phone,
            first_name=first_name,
            last_name=other_name
        )
        try:
            await client(ImportContactsRequest([contact]))
        except Exception as e:
            print(f"❌ Failed to import {phone}: {e}")
            continue

        # 7) Send two personalized messages
        for text in (
            f"🎂 Happy Birthday, {first_name}!",
            f"🎉 Congratulations, {other_name}!"
        ):
            try:
                await client.send_message(phone, text)
                print(f"✅ Sent to {phone}: {text}")
            except Exception as e:
                print(f"❌ Failed to send to {phone}: {e}")

    # 8) Disconnect when done
    await client.disconnect()

# 9) Execute the async main()
if __name__ == '__main__':
    asyncio.run(main())
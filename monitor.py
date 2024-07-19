import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, ChannelInvalidError, ChannelPrivateError, \
    ChannelPublicGroupNaError
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, InputPeerChannel

import database
from database import init_db
from database.models import User

api_id = 29569565
api_hash = 'ee9774481e8a1bd59ce3481c0d93cfe3'
phone_number = '+15153465234'
channel_id = -1002233906745  # Замените на ID вашего канала или username


async def main():
    await database.init_db()
    client = TelegramClient('anon', api_id, api_hash)

    await client.start(phone_number)

    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        try:
            await client.sign_in(phone_number, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    try:
        entity = await client.get_entity(channel_id)
    except (ValueError, ChannelInvalidError, ChannelPrivateError, ChannelPublicGroupNaError) as e:
        print(f"Failed to get entity for channel_id {channel_id}, error: {e}")
        return

    input_channel = InputPeerChannel(entity.id, entity.access_hash)

    while True:
        try:
            all_participants = await client(GetParticipantsRequest(
                input_channel, ChannelParticipantsSearch(''), 0, 100, hash=0
            ))

            user_ids_in_channel = [p.id for p in all_participants.users]

            users_in_db = await User.find({"user_id": {"$in": user_ids_in_channel}}).to_list()
            user_ids_in_db = {user.user_id for user in users_in_db}

            users_not_in_db = [user_id for user_id in user_ids_in_channel if user_id not in user_ids_in_db]

            print(f"Number of users not in database: {len(users_not_in_db)}")

        except Exception as e:
            print(f"Error during fetching participants: {e}")

        await asyncio.sleep(60)


if __name__ == '__main__':
    asyncio.run(main())

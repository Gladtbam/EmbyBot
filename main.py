from telethon.sync import TelegramClient
from app.tg import register_commands
from app.keyboard import register_callback
from app.data import load_config, load_user_msg_count
from app.scheduler import start_scheduler
from app.tgscore import score_commands, user_msg_count

# file_path = 'user_msg_count.json'

api_id = load_config()['API_ID']
api_hash = load_config()['API_HASH']
bot_token = load_config()['BOT_TOKEN']

# user_msg_count = load_user_msg_count(file_path)

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# 启动客户端
with client:
    register_commands(client)
    register_callback(client)
    score_commands(client)
    start_scheduler(client)
    client.run_until_disconnected()

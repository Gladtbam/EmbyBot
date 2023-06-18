from telethon.sync import TelegramClient
from app.tg import register_commands
from app.keyboard import register_callback
from app.db import load_config
from app.scheduler import start_scheduler
from app.tgscore import score_commands

api_id = load_config()['API_ID']
api_hash = load_config()['API_HASH']

bot_token = load_config()['BOT_TOKEN']

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# 启动客户端
with client:
    register_commands(client)
    register_callback(client)
    score_commands(client)
    start_scheduler(client)
    client.run_until_disconnected()

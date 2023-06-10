from telethon.sync import TelegramClient
from app.tg import register_commands
from app.keyboard import register_callback
from app.db import load_config
from app.scheduler import start_scheduler

# 填入你的API ID和API Hash
api_id = load_config()['API_ID']
api_hash = load_config()['API_HASH']

# 填入你的Token Bot Token
bot_token = load_config()['BOT_TOKEN']

# 创建使用 API ID 进行身份验证的 Telegram 客户端
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# 启动客户端
with client:
    register_commands(client)
    register_callback(client)
    start_scheduler()
    client.run_until_disconnected()

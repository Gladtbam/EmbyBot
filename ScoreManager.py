from Telegram import client
from LoadConfig import load_config
from telethon import events
from DataBase import GetUser

config = load_config()
@client.on(events.NewMessage(pattern=fr'^/checkin({config.telegram.BotName})?$'))
async def checkin(event):
    query = GetUser(event.sender_id)

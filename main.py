from telethon import TelegramClient, events
from app.telegram import handle_start, handle_help, handle_me, handle_info, handle_weblink
from app.emby_accouts import handle_signup_method, handle_code_check, handle_delete, handle_renew, handle_create_code, handle_nsfw, handle_resetpw, handle_create_code_right
from app.arr.search import handle_search, handle_add_search
from app.data import load_config
from app.scheduler import start_scheduler
from app.score_man import handle_new_message, handle_settle, handle_change_score, handle_checkin
from app.db import handle_get_renew
from app.notify.webhook import run_webhook
import asyncio

api_id = load_config()['Telegram']['API_ID']
api_hash = load_config()['Telegram']['API_HASH']
bot_token = load_config()['Telegram']['BOT_TOKEN']
bot_name = load_config()['Telegram']['BOT_NAME']
chat_id = load_config()['GROUP_ID']

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
client_user = TelegramClient('user', api_id, api_hash)

# 注册事件处理函数并传递client对象
client.add_event_handler(lambda event: handle_start(event), events.NewMessage(pattern=fr'^/start({bot_name})?$'))
client.add_event_handler(lambda event: handle_help(event), events.NewMessage(pattern=fr'^/help({bot_name})?$'))
client.add_event_handler(lambda event: handle_signup_method(client, event), events.NewMessage(pattern=fr'^/signup(?:{bot_name})?(\s.*)?$'))
client.add_event_handler(lambda event: handle_code_check(client, event), events.NewMessage(pattern=fr'^/code({bot_name})?\s+(.*)$'))
client.add_event_handler(lambda event: handle_delete(event), events.NewMessage(pattern=fr'^/del({bot_name})?$'))
client.add_event_handler(lambda event: handle_me(event), events.NewMessage(pattern=fr'^/me({bot_name})?$'))
client.add_event_handler(lambda event: handle_info(event), events.NewMessage(pattern=fr'^/info({bot_name})?$'))
client.add_event_handler(lambda event: handle_info(event), events.NewMessage(pattern=fr'^/info({bot_name})?$'))
client.add_event_handler(lambda event: handle_change_score(event), events.NewMessage(pattern=fr'^/change({bot_name})?\s+(.*)$'))
client.add_event_handler(lambda event: handle_checkin(client, event), events.NewMessage(pattern=fr'^/checkin({bot_name})?$'))
client.add_event_handler(lambda event: handle_search(client, event), events.NewMessage(pattern=fr'^/request(?:{bot_name})?(\s.*)?$'))

client.add_event_handler(lambda event: handle_new_message(event), events.NewMessage(chats=chat_id))

client.add_event_handler(lambda event: handle_renew(event), events.CallbackQuery(data='renew'))
client.add_event_handler(lambda event: handle_create_code(event), events.CallbackQuery(data='create_code'))
client.add_event_handler(lambda event: handle_nsfw(event), events.CallbackQuery(data='nsfw'))
client.add_event_handler(lambda event: handle_weblink(event), events.CallbackQuery(data='weblink'))
# client.add_event_handler(lambda event: handle_resetpw(event), events.CallbackQuery(data='reset_pw'))
client.add_event_handler(lambda event: handle_get_renew(event), events.CallbackQuery(data='get_renew'))
client.add_event_handler(lambda event: handle_get_renew(event), events.CallbackQuery(data='get_renew'))
client.add_event_handler(lambda event: handle_create_code_right(event), events.CallbackQuery(pattern=r'.*_code$'))
client.add_event_handler(lambda event: handle_add_search(client, event), events.CallbackQuery(pattern=r'^(movie_|tv_).*'))

client_user.add_event_handler(lambda event: start_scheduler(client_user))
client_user.add_event_handler(lambda event: handle_settle(client_user, event), events.NewMessage(pattern=fr'^/settle({bot_name})?$'))


async def run_telegram(client):
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    tasks = [run_telegram(client), run_telegram(client_user)]
    loop.run_until_complete(asyncio.gather(*tasks))
    
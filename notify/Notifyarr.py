from arr import *
from Telegram import client
from LoadConfig import init_config
import aiohttp
import asyncio
import logging
import traceback
import json
import os
from aiohttp import web
from jinja2 import Environment, FileSystemLoader, select_autoescape

config = init_config()
print(os.getcwd() + '/notify/templates')
env = Environment(
    loader=FileSystemLoader(os.getcwd() + '/notify/templates'),
    autoescape=select_autoescape(['html'])
)
routes = web.RouteTableDef()

@routes.post('/webhook')
async def handle_webhook(request):
    if request.body_exists:
        try:
            payload = await request.json()
            if payload.get('eventType') == 'Test':
                template = env.get_template('test.html')
                response = template.render(payload=payload)
                await client.send_message(config.telegram.NotifyChannel, response, parse_mode='HTML')
        except json.decoder.JSONDecodeError:
            return web.Response(text='Invalid JSON payload')

    return web.Response(text='Webhook received')

app = web.Application()
app.add_routes(routes)

async def run_webhook():
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 5000)
        await site.start()
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(e)



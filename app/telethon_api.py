from asyncio import sleep

async def reply(event, message, parse_mode='Markdown'):
    messages = await event.reply(message, parse_mode=parse_mode)
    await sleep(30)
    await messages.delete()

async def respond(event, message, parse_mode='Markdown', buttons=None):
    messages = await event.respond(message, parse_mode=parse_mode, buttons=buttons)
    await sleep(30)
    await messages.delete()
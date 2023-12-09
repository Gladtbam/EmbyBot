from Crypto.Cipher import AES
from time import time
import base64
import logging
from DataBase import GetCode, CreateCode, DeleteCode, GetUser, GetRenewValue, ChangeScore
from Telegram import client
from LoadConfig import init_config
from telethon import events, types, Button
import asyncio

config = init_config()
async def generate_code(s):
    timestamp = int(time())
    key = (str(timestamp) + '0' * (16 - len(str(timestamp)))).encode('utf-8')
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(s.encode('utf-8'))
    encoded = base64.b64encode(cipher.nonce + ciphertext).decode('utf-8')
    code = '-'.join([encoded[i:i+4] for i in range(0, len(encoded), 4)])
    try:
        await CreateCode(code, timestamp, base64.b64encode(tag).decode('utf-8'))
        return code
    except Exception as e:
        logging.error(f"创建码失败： {e}")
        return None

async def decrypt_code(code):
    try:
        _code = await GetCode(code)
        if _code is not None:
            timestamp = _code.TimeStamp
            tag = base64.b64decode(_code.Tag.encode('utf-8'))
            key = (str(timestamp) + '0' * (16 - len(str(timestamp)))).encode('utf-8')
            encoded = code.replace('-', '')
            decoded = base64.b64decode(encoded.encode('utf-8'))
            nonce = decoded[:16]
            ciphertext = decoded[16:]
            cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext.decode('utf-8')
        else:
            return None
    except ValueError as ve:
        logging.error(f"数据被篡改： {ve}")
        return None
    except Exception as e:
        logging.error(e)
        return None
    
@client.on(events.CallbackQuery(data='code_create'))
async def create_code(event):
    keyboard = [
            Button.inline('生成注册码', data='signup_code'),
            Button.inline('生成续期码', data='renew_code'),
    ]
    try:
        await event.respond('请选择生成的码类型\n使用前请先查看 WiKi, 否则造成的损失自付', buttons=keyboard)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        raise events.StopPropagation

@client.on(events.CallbackQuery(pattern=r'.*_code$'))
async def right_code(event):
    try:
        s = event.data.decode().split('_')[0]
        user = await GetUser(event.sender_id)
        value = await GetRenewValue()
        await event.answer(f"正在生成 {'续期码' if s == 'renew' else '注册码'}")
        if event.sender_id in config.other.AdminId or (user is not None and user.Score >= value):
            code = await generate_code(s)
            if code is not None:
                await client.send_message(event.sender_id, f"{'续期码' if s == 'renew' else '注册码'}生成成功\n`{code}`")
                await ChangeScore(event.sender_id, -(value if event.sender_id not in config.other.AdminId else 0))
            else:
                await event.respond(f"{'续期码' if s == 'renew' else '注册码'}生成失败")
        else:
            await event.respond(f"积分不足, 生成失败")
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # raise events.StopPropagation
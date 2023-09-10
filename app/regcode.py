import base58
from nacl import signing, hash, exceptions
from telethon import Button
from datetime import datetime, timedelta
from asyncio import sleep
from app.db import create_code
from app.db import change_score, search_score, init_renew_value
from app.data import load_config
from app.telethon_api import reply, respond

admin_ids = load_config()['ADMIN_IDS']

# 生成注册码、续期码
async def generate_code(tgid, func_bit):                            #func_bit: 1为注册码，0为续期码
    data = str(func_bit) + str(tgid)

    encode_data = base58.b58encode(data.encode('utf-8'))            # 使用 Base58 编码
    sha256_data = hash.sha256(encode_data)                          # 计算出编码后的 SHA256
    signing_key = signing.SigningKey.generate()                     # 生成签名私钥
    signed_data = signing_key.sign(sha256_data)                     # 对 SHA256 签名

    code = base58.b58encode(signed_data.signature)                  # 生成的 码
    pub_key = signing_key.verify_key.encode()
    public_key = base58.b58encode(pub_key)  # 公钥，用于校验 码
    hash_sha256 = base58.b58encode(sha256_data)

    return code.decode('utf-8'), public_key.decode('utf-8'), hash_sha256.decode('utf-8')

# 解码注册码、续期码
async def verify_code(code, public_key, sha256_hash):
    signed_data = base58.b58decode(code)                            # 解码 Base58
    public_key_d = base58.b58decode(public_key)
    signed_sha256 = base58.b58decode(sha256_hash)

    verifying_key = signing.VerifyKey(public_key_d)

    try:
        verifying_key.verify(signed_sha256, signed_data)           # 验证签名
        return True
    except Exception as e:
        print(f"Exception occurred: {e}")
        return False

async def handle_create_code(event):
    keyboard = [
        Button.inline("注册码", b"activation_code"),
        Button.inline("续期码", b"renew_code")
    ]
    await respond(event, f'点击生成注册码或续期码\n使用前请先查看 WiKi, 否则造成的损失自付', buttons=keyboard)

async def handle_create_code_right(event):
    tgid = event.sender_id
    print(event.data.decode())

    if event.data == b'renew_code':
        func_bit = 0
    elif event.data == b'activation_code':
        func_bit = 1
    else:
        func_bit = 9
        await reply(event, '无法创建正确的码')
    result = await search_score(tgid)
    value = int(init_renew_value())

    if func_bit == 0:
        await event.answer('正在生成续期码！')
    elif func_bit == 1:
        await event.answer('正在生成注册码！')

    code, public_key, sha256_hash = await generate_code(tgid, func_bit)

    if tgid in admin_ids:
        code_time = datetime.now().date() + timedelta(days=90)
    else:
        code_time = datetime.now().date() + timedelta(days=30)
        if result is not None and result[1] > value:
            await change_score(tgid, -(value))
        else:
            await respond(event, "积分不足, 无法生成")
            
    if tgid in admin_ids or (result is not None and result[1] > value):
        await create_code(code, public_key, sha256_hash, func_bit, code_time)
        if func_bit == 0:
            await event.respond(f"你生成的续期码为:(点击复制) \n`{code}`\n有效期至 {code_time}")
        elif func_bit == 1:
            await event.respond(f"你生成的注册码为:(点击复制) \n`{code}`\n有效期至 {code_time}")

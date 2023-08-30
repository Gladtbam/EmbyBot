import base58
from nacl import signing, hash, exceptions

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

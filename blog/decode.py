import json
import markdown

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import base64

def decode_post(msg, privkey, enckey):
    dkey = RSA.importKey(privkey)
    key = dkey.decrypt(enckey)
    aes = AES.new(key)
    msg = aes.decrypt(base64.b64decode(msg))
    msg = msg.strip()
    msg = json.loads(msg)
    return msg

def dump_html(content):
    ret = markdown.markdown(content)
    return ret



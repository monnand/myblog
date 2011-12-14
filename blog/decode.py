import json
import markdown

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import base64

def decode_post(msg, privkey, enckey):
    dkey = RSA.importKey(privkey)
    enckey = base64.b64decode(enckey)
    key = dkey.decrypt(enckey)
    aes = AES.new(key, AES.MODE_CBC)
    msg = base64.b64decode(msg)
    msg = aes.decrypt(msg)
    msg = msg.strip()
    msg = json.loads(msg)
    return msg

def dump_html(content, content_format):
    ret = markdown.markdown(content)
    return ret



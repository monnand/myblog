import json
import markdown

from Crypto.PublicKey import RSA

def decode_post(msg, key):
    dkey = RSA.importKey(key)
    msg = dkey.decrypt(msg)
    msg = json.loads(msg)
    return msg

def dump_html(content):
    ret = markdown.markdown(content)
    return ret



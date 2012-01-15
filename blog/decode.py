import json
import markdown

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import base64

def decode_post(msg, privkey, enckey):
    try:
        dkey = RSA.importKey(privkey)
        enckey = base64.b64decode(enckey)
        key = dkey.decrypt(enckey)
        aes = AES.new(key, AES.MODE_CBC)
        msg = base64.b64decode(msg)
        msg = aes.decrypt(msg)
        msg = msg.strip()
        msg = json.loads(msg)
        return msg
    except:
        return None

def dump_html(content, content_format):
    if content_format == 'html':
        return content
    md = markdown.Markdown(extensions = ['footnotes', \
            'codehilite', 'headerid(level=3)'])
    ret = md.convert(content)
    return ret



import urllib2
import urllib
from Crypto.PublicKey import RSA

import json
import base64
import sys

def load_key_value(line, data):
    line = line.strip()
    if len(line) == 0:
        return False
    pair = line.split(":")
    key = pair[0].lower()
    value = pair[1].strip()

    data[key] = value
    return True

def load_blog_file(filename):
    data = {}
    f = open(filename, "r")

    line = f.readline()
    while line:
        if not load_key_value(line, data):
            break
        line = f.readline()

    kf = open(data['key'], "r")
    del data['key']
    key = kf.read()
    kf.close()

    content = f.read()
    data['content'] = content
    data['content_format'] = 'markdown'
    jmsg = json.dumps(data)

    en = RSA.importKey(key)
    encrypt_msg = en.encrypt(jmsg, "")

    b64msg = base64.b64encode(encrypt_msg)

    msg = {}
    msg['msg'] = b64msg
    msg['author'] = data['author']

    return urllib.urlencode(msg)

if __name__ == "__main__":
    url = "http://127.0.0.1:8000/post_blog/"

    filename = sys.argv[1]
    data = load_blog_file(filename)
    print filename


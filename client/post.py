#!/usr/bin/python2

import urllib2
import urllib
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto import Random

import json
import base64
import sys

def load_key_value(line, data):
    line = line.strip()
    if len(line) == 0:
        return False
    pair = line.split(":")
    if len(pair) != 2:
        return True
    key = pair[0].lower()
    value = pair[1].strip()

    if key == 'tags':
        value = json.loads(value)

    data[key] = value
    return True

def pad_msg(msg, block_size):
    p = " "
    return msg + (block_size - len(msg) % block_size) * p

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

    block_size = 32
    symkey = Random.new().read(block_size)
    b64symkey = en.encrypt(symkey, "")
    b64symkey = base64.b64encode(b64symkey[0])
    print "base64ed key: ", b64symkey

    cipher = AES.new(symkey, AES.MODE_CBC)
    jmsg = pad_msg(jmsg, block_size)
    print "padded message: ", jmsg
    encrypt_msg = cipher.encrypt(jmsg)
    b64msg = base64.b64encode(encrypt_msg)
    print "b64ed message: ", b64msg

    msg = {}
    msg['msg'] = b64msg
    msg['author'] = data['author']
    msg['key'] = b64symkey

    return urllib.urlencode(msg)

if __name__ == "__main__":
    url = "http://127.0.0.1:8000/postblog/"
    if len(sys.argv) > 2:
        url = "http://" + sys.argv[2] + "/postblog/"

    filename = sys.argv[1]
    data = load_blog_file(filename)

    c = urllib2.urlopen(url, data)
    c.read()


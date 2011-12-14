import urllib2
import urllib
from Crypto.PublicKey import RSA
from Crypto import Random
import json

# private key is decrypt key.
# public key is encrypt key.

if __name__ == "__main__":
    url = "http://127.0.0.1:8000/newauthor/"
    data = {}
    rng = Random.new().read

    keys = RSA.generate(1024, rng)
    decrypt_key = keys
    decrypt_key_pem = decrypt_key.exportKey()
    data['decrypt_key'] = decrypt_key_pem

    encrypt_key = keys.publickey()
    encrypt_key_pem = encrypt_key.exportKey()

    name = raw_input("User Name: ")
    name = name.strip()
    data['name'] = name
    keyf = open(name + ".pem", "w+")

    email = raw_input("Email: ")
    email = email.strip()
    data['email'] = email

    about = raw_input("About: ")
    about = about.strip()
    data['about'] = about

    msg = {}
    msg['msg'] = json.dumps(data)
    msg['author'] = name
    msg['key'] = ""

    c = urllib2.urlopen(url, urllib.urlencode(msg))

    print c.read()

    print "--------------"
    print encrypt_key_pem
    keyf.write(encrypt_key_pem)
    keyf.close()


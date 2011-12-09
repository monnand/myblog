import json
import markdown

def decode_post(msg, key):
    msg = json.loads(msg)
    return msg

def dump_html(content):
    ret = markdown.markdown(content)
    return ret



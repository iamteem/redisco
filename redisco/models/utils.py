import base64

def _encode_key(s):
    return base64.b64encode(s).replace("\n", "")

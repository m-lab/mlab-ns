import base64
import hashlib
import hmac
import string
import time
import logging

def sign_message(data, key):
    """Computes a signature of the data in input.
    
    It first sorts the keys of the dictionary and than concatenates the
    content of the data. Then computes a hmac digest over the resulting
    string, using the 'key' in input.
    
    Args:
        key: A string representing the key that is used to compute
            the signature.
    
    Return:
        A string representing the signature.
    """
    value_list = []
    for i in sorted(data.iterkeys()):
        logging.debug(data[i])
        value_list.append(data[i])
    
    key = key.encode('ascii')
    values_str = string.join(value_list, '')
    digest = hmac.new(key, values_str, hashlib.sha1).digest()
    signature = base64.encodestring(digest).strip()
    logging.debug(signature)

    return signature

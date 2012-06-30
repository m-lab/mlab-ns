import base64
import hashlib
import hmac
import string
import time

def validate(data, key, expected_signature):
    """Checks the signature of a request.
    
    It first sort the keys of the dictionary and than concatenates the
    content of the data. Then computes a hmac digest over the resulting
    string, using the 'key' in input and compares it with the 
    'expected_signature'.
    
    Args:
        data: A dict containing the request data.
        key: A string representing the key that must be used to verify
            the signature.
        expected_signature: A string representing the signature of the
            data that must match.
      
    Return:
        True if the computed signature matches the expected one and False
        otherwise.
    """
    str_list = []
    for argument in sorted(data.iterkeys()):
        str_list.append(data[argument])  
    
    message = string.join(str_list, '')
    key = key.encode('ascii')
    digest = hmac.new(key, message, hashlib.sha1).digest()
    signature = base64.encodestring(digest).strip() 
    
    return (signature == expected_signature)

def sign(data, key):
    """Computes a signature over the data in input.
    
    It first sort the keys of the dictionary and than concatenates the
    content of the data. Then computes a hmac digest over the resulting
    string, using the 'key' in input.
    
    Args:
        key: A string representing the key that must be used to compute
            the signature.
    
    Return:
        A string representing the signature.
    """
    str_list = []
    for argument in sorted(data.iterkeys()):
        str_list.append(data[argument])
    
    message = string.join(str_list, '')
    digest = hmac.new(key, message, hashlib.sha1).digest()
    signature = base64.encodestring(digest).strip()
    key = key.encode('ascii')
    return signature
    
def generate_timestamp():
    """Seconds since epoch(UTC).
    
    Return:
        A string containing the timestamp in seconds since epoch(UTC).
    """
    return str(int(time.time()))

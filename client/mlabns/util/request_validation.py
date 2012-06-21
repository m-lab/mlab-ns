import base64
import hmac
import hashlib
import time

def validate(data, key, expected_signature):
    """Checks the signature of a request.

    It first sort the keys of the dictionary and than concatenates the content
    of the data. Then computes a hmac digest over the resulting string, using
    the 'key' in input and compares it with the 'expected_signature'.

    Args:
        data: A dict containing the request data.
        key: The key that must be used to verify the signature.
        expected_signature: Signature of the data that must match.

    Return:
        True if the computed signature matches the expected one and False
        otherwise.
    """
    for argument in sorted(data.iterkeys()):
        # TODO(claudiu) Use a list and join, instead of +=
        message += data[argument]
  
    key = key.encode('ascii')
    digest = hmac.new(key, message, hashlib.sha1).digest()
    signature = base64.encodestring(digest).strip() 
    
    return (signature == expected_signature)

def sign(data, key):
    """Computes a signature over the data in input.

    It first sort the keys of the dictionary and than concatenates the content
    of the data. Then computes a hmac digest over the resulting string, using
    the 'key' in input.

    Args:
        key: The key that must be used to compute the signature.

    Return:
        A string representing the signature.
    """
    message = ''
    for argument in sorted(data.iterkeys()):
        # TODO(claudiu) Use a list and join instead of +=
        message = message + data[argument]  
  
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

def fake_headers():
    """For debug purposes, add fake geolocation data and user_gent.
    
    Return:
        A dict containing the headers.
    """
    headers = {}
    headers['user_agent'] = "Mozilla/5.0"
    headers['X-AppEngine-City'] = "City"
    headers['X-AppEngine-Region'] = "Region"
    headers['X-AppEngine-Country'] = "Country"
    headers['X-AppEngine-CityLatLong'] = "0,0"
    return headers

import os

# Add any libraries in the "mlabns/third_party" directory.
from google.appengine.ext import vendor

# Convoluted path as suggested from GAE documentation:
# https://cloud.google.com/appengine/docs/standard/python/tools/using-libraries-python-27#requesting_a_library
vendor.add(os.path.join(os.path.dirname(os.path.realpath(__file__)),
    'mlabns/third_party/geoip2'))
vendor.add(os.path.join(os.path.dirname(os.path.realpath(__file__)),
    'mlabns/third_party/GoogleAppEngineCloudStorageClient'))

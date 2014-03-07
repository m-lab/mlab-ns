from google.appengine.api import memcache

from mlabns.db import model
from mlabns.util import constants
from mlabns.util import message

import logging

class Sieve:
    def __init__(self, attribute, value):
        self.value = value
        self.attribute = attribute
    def sieve(self, candidates):
        new_candidates = []
        if self.value == None or self.attribute == None:
            return candidates

        for candidate in candidates:
            #Check for the attribute's presence.
            if hasattr(candidate, self.attribute):
                value = getattr(candidate, self.attribute)
                #Check to see if the attribute's value matches the sieve
                if (value == self.value):
                    logging.error("Keeping candidate %s because %s does match %s" % (candidate, self.value, value))
                    new_candidates.append(candidate) 
                else:
                    logging.error("Removing candidate %s because %s does not match %s" % (candidate, self.value, value))
            #Remove candidates that do not even have that attribute defined.
            else:
                logging.error("Removing candidate %s because it does not have %s attribute." % (candidate, self.attribute))

        return new_candidates

def new_sieves_from_request(sieve_request):
    sieves = []

    if sieve_request == None:
        return sieves

    for sieve_parameter in sieve_request.split('~'):
        sieve_parameter_split = sieve_parameter.split(':')
        if len(sieve_parameter_split) != 2:
            continue
        sieve_attribute = sieve_parameter_split[0]
        sieve_value = sieve_parameter_split[1]
        logging.error("Making sieve with attribute %s and value %s" % (sieve_attribute, sieve_value))
        sieves.append(Sieve(sieve_attribute, sieve_value))

    return sieves

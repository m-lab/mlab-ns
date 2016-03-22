from google.appengine.api import memcache

import logging

from mlabns.db import model
from mlabns.util import constants


def get_nagios_credentials():
    """Function to retrieve nagios authentication information. 
    First checks cache, if no hit checks datastore.

    Returns: 
        (Nagios): Nagios model instance containing nagios credentials,
    """
    nagios = memcache.get(constants.DEFAULT_NAGIOS_ENTRY)
    if not nagios:
        nagios = model.Nagios.get_by_key_name(constants.DEFAULT_NAGIOS_ENTRY)
        if nagios:
            memcache.set(constants.DEFAULT_NAGIOS_ENTRY, nagios)
        else:
            logging.error('Datastore does not have the Nagios credentials.')

    return nagios


def get_tools_by_id():
    """Function to retrieve tools by id. First checks cache, if no hit checks
	datastore. 

	Returns: 
		(iterator) of Tool instances
	"""
    tools = memcache.get('tools_by_id')
    if not tools:
        tools = list(model.Tool.gql('ORDER by tool_id DESC').run(
            batch_size=constants.GQL_BATCH_SIZE))
        if not memcache.set('tools_by_id', tools):
            logging.error('Failed to update tools by id in memcache.')

    return tools


def get_SliverTool_by_tool_id(tool_id):
    """Function to retrieve SliverTools by tool_id. First checks cache, if no hit checks
	datastore. 

	Returns: 
		(iterator) of SliverTool instances
	"""
    sliver_tool_key = 'sliver_tool_tool_id_{}'.format(tool_id)
    sliver_tools = memcache.get(sliver_tool_key)

    if not sliver_tools:
        sliver_tools = list(model.SliverTool.gql(
            'WHERE tool_id=:tool_id',
            tool_id=tool_id).run(batch_size=constants.GQL_BATCH_SIZE))
        if not memcache.set(sliver_tool_key, sliver_tools):
            logging.error('Failed to update sliver status in memcache.')

    return sliver_tools

#! /usr/bin/env python

# The design documentation can be found at http://goo.gl/48S22.

import ConfigParser
import logging
import string
import time
import urllib
import urllib2
import socket

from optparse import OptionParser
from os import R_OK
from os import access
from os import path


def get_config(filename):
    config = ConfigParser.ConfigParser()
    try:
        fp = open(filename)
    except IOError:
        logging.error(
            'Cannot open the configuration file: %s.',
            filename)
        exit(-1)
    try:
        config.readfp(fp)
    except ConfigParser.Error:
        # TODO(claudiu) Trigger an event/notification.
        logging.error(
            'Cannot read the configuration file: %s.',
            filename)
        exit(-1)
    fp.close()
    return config


def read_mlab_tools(filename):
    config = get_config(filename)
    mlab_tools = {}
    for section in config.sections():
        mlab_tool = {}
        for option in config.options(section):
            mlab_tool[option] = config.get(section, option)
        mlab_tools[section] = mlab_tool

    return mlab_tools


def read_mlab_sites(filename):
    config = get_config(filename)
    mlab_sites = {}
    for section in config.sections():
        mlab_site = {}
        for option in config.options(section):
            mlab_site[option] = config.get(section, option)
        mlab_sites[mlab_site['site_id']] = mlab_site

    return mlab_sites

def read_mlab_slices(filename):
    """Read slices from file.

    Each slice is a dict with 'slice_id' 'tool_id'.

    """
    config = get_config(filename)
    mlab_slices = {}
    for section in config.sections():
        slice_id = config.get(section, 'slice_id')
        tool_id = config.get(section, 'tool_id')

        if slice_id not in mlab_slices:
            mlab_slices[slice_id] = set([])
        mlab_slices[slice_id].add(tool_id)
    return mlab_slices

def read_mlab_slivers_ipv4(filename):
    config = get_config(filename)
    slivers = {}
    for section in config.sections():
        for option in config.options(section):
            ip = config.get(section, option)
            parts = option.split('.')
            server_id= parts[0]
            site_id = parts[1]
            sliver_id = '-'.join([
                section,
                server_id,
                site_id])

            slivers[sliver_id] = {}
            slivers[sliver_id]['sliver_id'] = sliver_id
            slivers[sliver_id]['server_id'] = server_id
            slivers[sliver_id]['site_id'] = site_id
            slivers[sliver_id]['slice_id'] = section
            slivers[sliver_id]['sliver_ipv4'] = 'off'
            slivers[sliver_id]['sliver_ipv6'] = 'off'

            try:
                socket.inet_pton(socket.AF_INET, ip)
                slivers[sliver_id]['sliver_ipv4'] = ip
            except socket.error:
                pass
    return slivers

def read_mlab_slivers_ipv6(filename):
    config = get_config(filename)
    slivers = {}
    for section in config.sections():
        for option in config.options(section):
            ip = config.get(section, option)
            parts = option.split('.')
            server_id = parts[0]
            site_id = parts[1]
            sliver_id = '-'.join([
                section,
                server_id,
                site_id])

            slivers[sliver_id] = {}
            slivers[sliver_id]['sliver_id'] = sliver_id
            slivers[sliver_id]['server_id'] = server_id
            slivers[sliver_id]['site_id'] = site_id
            slivers[sliver_id]['slice_id'] = section
            slivers[sliver_id]['sliver_ipv6'] = 'off'
            slivers[sliver_id]['sliver_ipv4'] = 'off'

            try:
                socket.inet_pton(socket.AF_INET6, ip)
                slivers[sliver_id]['sliver_ipv6'] = ip
            except socket.error:
                pass
    return slivers

def main():
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.DEBUG)

    parser = OptionParser()
    parser.add_option(
        '',
        '--sites',
        dest='file_sites',
        help='Name of the file containig the sites.')

    parser.add_option(
        '',
        '--slices',
        dest='file_slices',
        help='Name of the file containig the slices.')

    parser.add_option(
        '',
        '--slivers-ipv4',
        dest='file_slivers_ipv4',
        help='Name of the file containig the slivers.')

    parser.add_option(
        '',
        '--slivers-ipv6',
        dest='file_slivers_ipv6',
        help='Name of the file containig the slivers.')

    parser.add_option(
        '',
        '--tools',
        dest='file_tools',
        help='Name of the file containig the tools configuration.')

    parser.add_option(
        '',
        '--out',
        dest='file_out',
        default='sliver_tools.txt',
        help='Name of the output file containing the sliver tools.')

    (options, args) = parser.parse_args()
    if options.file_sites is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing sites configuration file.')
        parser.print_help()
        exit(-1)

    if options.file_slices is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing slices configuration file.')
        parser.print_help()
        exit(-1)

    if options.file_slivers_ipv4 is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing slivers ipv4 configuration file.')
        parser.print_help()
        exit(-1)

    if options.file_slivers_ipv6 is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing slivers ipv6 configuration file.')
        parser.print_help()
        exit(-1)

    if options.file_tools is None:
        # TODO(claudiu) Trigger an event/notification.
        logging.error('Missing tools configuration file.')
        parser.print_help()
        exit(-1)


    sites = read_mlab_sites(options.file_sites)
    slices = read_mlab_slices(options.file_slices)
    slivers = read_mlab_slivers_ipv4(options.file_slivers_ipv4)
    slivers_ipv6 = read_mlab_slivers_ipv6(options.file_slivers_ipv6)
    tools = read_mlab_tools(options.file_tools)

    for i in slivers_ipv6:
        slivers[i]['sliver_ipv6'] = slivers_ipv6[i]['sliver_ipv6']

    for sliver in slivers.itervalues():
        if sliver['site_id'] not in sites:
            continue
        for tool in slices[sliver['slice_id']]:
            record = {}
            parts = sliver['slice_id'].split('_')
            record['fqdn'] = '.' . join([
                parts[1],
                parts[0],
                sliver['server_id'],
                sliver['site_id'],
                'measurement-lab.org'])
            record['entity'] = 'sliver_tool'
            record['tool_id'] = tool
            record['site_id'] = sliver['site_id']
            record['slice_id'] = sliver['slice_id']
            record['server_id'] = sliver['server_id']
            record['server_port'] = tools[tool]['server_port']
            record['http_port'] = tools[tool]['http_port']
            record['sliver_tool_key'] = tools[tool]['tool_key']
            record['sliver_ipv4'] = sliver['sliver_ipv4']
            record['sliver_ipv6'] = sliver['sliver_ipv6']
            record['url'] = 'off'
            if (record['http_port'] != 'off'):
                record['url'] = ''.join([
                    'http://',
                    record['fqdn'],
                    ':',
                    record['http_port']])
            record['status'] = 'init'
            if sliver['site_id'] in sites:
                record['lat_long'] = sites[sliver['site_id']]['lat_long']
            else:
                record['lat_long'] = '0,0'
            record ['id'] = '-'.join([tool, sliver['sliver_id']])

            print '[%s]' % (record['id'])
            print 'entity: %s' % (record['entity'])
            print 'fqdn: %s' % (record['fqdn'])
            print 'tool_id: %s' % (record['tool_id'])
            print 'site_id: %s' % (record['site_id'])
            print 'slice_id: %s' % (record['slice_id'])
            print 'server_id: %s' % (record['server_id'])
            print 'server_port: %s' % (record['server_port'])
            print 'http_port: %s' % (record['http_port'])
            print 'sliver_tool_key: %s' % (record['sliver_tool_key'])
            print 'sliver_ipv4: %s' % (record['sliver_ipv4'])
            print 'sliver_ipv6: %s' % (record['sliver_ipv6'])
            print 'url: %s' % (record['url'])
            print 'status: %s' % (record['status'])
            print 'lat_long: %s' % (record['lat_long'])
            print '\n'

if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""Compares the results from two different mlab-ns instances."""

import argparse
import json
import logging
import sys
import urllib2

QUERY_STRING = 'policy=all'


def parse_options(args):
    """Parses the options passed to this script.

    Args:
        args: list of options passed on command line

    Returns:
        An argparse.ArgumentParser object containing the passed options and
        their values.
    """
    parser = argparse.ArgumentParser(
        description='Compares the results from two different mlab-ns instances.')
    parser.add_argument(
        '--instance_one_url',
        dest='instance_one_url',
        default='http://mlab-ns.appspot.com',
        help='Base URL for the first mlab-ns instance to query.')
    parser.add_argument(
        '--instance_two_url',
        dest='instance_two_url',
        default='http://mlab-nstesting.appspot.com',
        help='Base URL for the second mlab-ns instance to query.')
    parser.add_argument('--tool_id',
                        dest='tool_id',
                        default='ndt',
                        help='The tool_id to query e.g., ndt.')
    parser.add_argument('--all_fields',
                        dest='all_fields',
                        action="store_true",
                        help='Whether to compare all fields or just "fqdn".')

    args = parser.parse_args(args)

    return args


def get_mlabns_status(url):
    """Fetches experiment status data from mlab-ns in JSON format.
    
    Arguments:
        url: str, URL for fetching status data from mlab-ns.
    
    Returns:
        dict: status information for the tool.
    """
    try:
        request = urllib2.urlopen(url)
        raw_data = request.read()
    except urllib2.HTTPError:
        logging.error('Cannot connect to %s', url)
        sys.exit(1)

    try:
        json_data = json.loads(raw_data)
    except ValueError:
        logging.error('Could not parse JSON from %s', url)
        sys.exit(1)

    return json_data


def convert_sort_results(results, args):
    results_list = []
    for result in sorted(results, key=lambda d: d['fqdn']):
        # TODO (kinkade): make this work for IPv6 too.
        # result['ip'] is a list with the first item being the IPv4 address and
        # the second the IPv6, if one exists.
        if args.all_fields:
            item = [
                result['city'], result['country'], result['fqdn'],
                result['ip'][0], result['site'], result['url']
            ]
        else:
            item = [result['fqdn']]

        results_list.append(item)

    result_set = set(tuple(row) for row in results_list)
    return result_set


def compare_results(s1, s2):
    s1_not_s2 = s1.difference(s2)
    s2_not_s1 = s2.difference(s1)

    print 'Instance 1 and 2 agree on %d services.' % len(s1.intersection(s2))
    print 'Instance 1 advertises these services which instance 2 does not:'
    for item in sorted(s1_not_s2):
        print '    %s' % (item,)

    print 'Instance 2 advertises these services which instance 1 does not:'
    for item in sorted(s2_not_s1):
        print '    %s' % (item,)


def main():
    args = parse_options(sys.argv[1:])

    url_one = '%s/%s?%s' % (args.instance_one_url, args.tool_id, QUERY_STRING)
    results_one = get_mlabns_status(url_one)
    logging.info('Results returned from instance one: %d', len(results_one))
    set_one = convert_sort_results(results_one, args)

    url_two = '%s/%s?%s' % (args.instance_two_url, args.tool_id, QUERY_STRING)
    results_two = get_mlabns_status(url_two)
    logging.info('Results returned from instance two: %d', len(results_two))
    set_two = convert_sort_results(results_two, args)

    compare_results(set_one, set_two)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""Compares the results from two different mlab-ns instances."""

import argparse
import json
import logging
import re
import sys
import time
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
        description='Compares the results from two mlab-ns instances.')
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
    parser.add_argument(
        '--all_fields',
        dest='all_fields',
        action="store_true",
        help='Compare all fields for equality, not just "fqdn".')
    parser.add_argument(
        '--infer_queueing',
        dest='infer_queueing',
        action="store_true",
        help='Attempts to determine if queueing accounts for differences.')
    parser.add_argument('--verbose',
                        dest='verbose',
                        action="store_true",
                        help='Whether to print extra information.')
    parser.add_argument('--ignore_pattern',
                        dest='ignore_patterns',
                        nargs='*',
                        default=[],
                        help='Regex pattern to ignore, matched against "fqdn".')

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


def filter_results(results, args):
    """Filters results for any the user didn't want processed.
    
    Arguments:
        results: list of dicts, with each dict containing status for a service.
        args: argparse.ArgumentParser, options passed to script.
    
    Returns:
        list: with any matching items filtered.
    """
    # Before processing the result list, check to see if the 'fqdn'
    # field matches any --ignore_pattern options that may have been supplied by
    # the user.
    filtered_results = []
    for key, status in enumerate(results):
        matched = False
        for pattern in args.ignore_patterns:
            if re.search(pattern, status['fqdn']):
                matched = True

        if not matched:
            filtered_results.append(results[key])

    return filtered_results


def infer_queueing(results1, results2):
    """Makes a loose determination of whether NDT node is queueing.

    NOTE: This function is temporary and highly specific to comparing Nagios status to Prometheus status, AND is only relevant for --tool_id=ndt. Nagios does not know whether NDT is queueing or not, whereas Prometheus has a check for this, and will fail NDT if it detects that queueing is happening. This function dumbly assumes that Nagios (results1) is advertising mlab1, and if Prometheus (results2) is advertising anything other than mlab1 for the same site, then we assume it has detected queueing.

    Arguments:
        results1: list of dicts, with each dict containing status for a service.
        results2: list of dicts, with each dict containing status for a service.

    Returns:
        list, list of dicts with possible NDT queueing reconciled.
    """
    munged_results2 = []
    for result1 in results1:
        r1_node, r1_site = re.search('(mlab[1-4])\.([a-z]{3}[0-9]{2})',
                                     result1['fqdn']).groups()
        for result2 in results2:
            r2_node, r2_site = re.search('(mlab[1-4])\.([a-z]{3}[0-9]{2})',
                                         result2['fqdn']).groups()
            if r1_site == r2_site:
                if r1_node < r2_node:
                    munged_results2.append(result1)
                else:
                    munged_results2.append(result2)
            else:
                munged_results2.append(result2)

    return munged_results2


def convert_results(results, args):
    """Converts JSON results into a python set().
    
    Arguments:
        results: list of dicts, with each dict containing status for a service.
        args: argparse.ArgumentParser, options passed to script.
    
    Returns:
        set: representing the results passed to function.
    """
    results_list = []
    for result in results:
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

        results_list.append(tuple(item))

    return set(results_list)


def compare_results(s1, s2):
    """Compares two sets.
    
    Arguments:
        s1: set, first set for comparison.
        s2: set, first set for comparison.
    
    Returns:
        dict, data with comparison results for sets.
    """
    data = {}
    data['s1_not_s2'] = s1.difference(s2)
    data['s2_not_s1'] = s2.difference(s1)
    data['s1_and_s2'] = s1.intersection(s2)

    return data


def main():
    args = parse_options(sys.argv[1:])

    samples = 0
    s1_count_total = 0
    s1_and_s2_total = 0
    s1_not_s2_total = 0
    s2_not_s1_total = 0

    while samples < 10:
        url_one = '%s/%s?%s' % (args.instance_one_url, args.tool_id,
                                QUERY_STRING)
        results_one = get_mlabns_status(url_one)
        results_one_filtered = filter_results(results_one, args)

        url_two = '%s/%s?%s' % (args.instance_two_url, args.tool_id,
                                QUERY_STRING)
        results_two = get_mlabns_status(url_two)
        results_two_filtered = filter_results(results_two, args)

        if args.infer_queueing:
            results_two_filtered = infer_queueing(results_one_filtered,
                                                  results_two_filtered)

        set_one = convert_results(results_one_filtered, args)
        set_two = convert_results(results_two_filtered, args)

        data = compare_results(set_one, set_two)

        samples = samples + 1

        # Calculate counts and totals
        s1_count = len(set_one)
        s1_and_s2_count = len(data['s1_and_s2'])
        s1_not_s2_count = len(data['s1_not_s2'])
        s2_not_s1_count = len(data['s2_not_s1'])
        s1_count_total = s1_count_total + s1_count
        s1_and_s2_total = s1_and_s2_total + len(data['s1_and_s2'])
        s1_not_s2_total = s1_not_s2_total + len(data['s1_not_s2'])
        s2_not_s1_total = s2_not_s1_total + len(data['s2_not_s1'])

        # Current
        print '## SAMPLE %d' % samples
        print 'Instance 1 count: %d' % s1_count
        print 'Instance 1 AND instance 2: %d' % s1_and_s2_count
        print 'Instance 1 NOT instance 2: %d' % s1_not_s2_count
        if args.verbose:
            for item in data['s1_not_s2']:
                print '    %s' % item
        print 'Instance 2 NOT instance 1: %d' % s2_not_s1_count
        if args.verbose:
            for item in data['s2_not_s1']:
                print '    %s' % item
        discrepancy_1_2 = s1_not_s2_count / (s1_count * 1.0) * 100
        print 'Discrepancy between 1 and 2: {0:.2f}%'.format(discrepancy_1_2)
        discrepancy_2_1 = s2_not_s1_count / (s1_count * 1.0) * 100
        print 'Discrepancy between 2 and 1: {0:.2f}%'.format(discrepancy_2_1)

        # Averages
        print '## AVERAGES (since start)'
        print 'Instance 1 count: %d' % (s1_count_total / samples)
        print 'Instance 1 AND instance 2: %d' % (s1_and_s2_total / samples)
        print 'Instance 1 NOT instance 2: %d' % (s1_not_s2_total / samples)
        print 'Instance 2 NOT instance 1: %d' % (s2_not_s1_total / samples)
        discrepancy_1_2_avg = (s1_not_s2_total / samples) / (
            s1_count_total / samples * 1.0) * 100
        print 'Discrepancy between 1 and 2: {0:.2f}%'.format(
            discrepancy_1_2_avg)
        discrepancy_2_1_avg = (s2_not_s1_total / samples) / (
            s1_count_total / samples * 1.0) * 100
        print 'Discrepancy between 2 and 1: {0:.2f}%\n\n'.format(
            discrepancy_2_1_avg)

        # Sleep for 60s
        time.sleep(60)


if __name__ == '__main__':
    main()
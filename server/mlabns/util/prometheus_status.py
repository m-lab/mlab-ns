import json
import logging
import textwrap
import urllib
import urllib2

from mlabns.util import constants
from mlabns.util import message

# This global dict maps tool_ids to the corresponding Prometheus query that
# will return the status for that tool.
#
# NOTE: These queries are rather unintuitive and bear some explanation. A
# previous iteration of the queries was using the `OR` operator to join
# vectors. However, the `OR` operator has a behavior which makes it unsuitable
# for use with these queries. The `OR` operator will exclude timeseries, except
# the first, with matching labelsets. Because, in the case of the NDT queries,
# the last two vectors (vdlimit_* and lame_duck_experiment) are both
# node_exporter metrics, they have matching label sets. This meant that the
# lame_duck_experiment vector was getting excluded, making it impossible to
# remove a node from mlab-ns rotation via the lame-duck mechanism.
#
# The current format adds the value of the vectors. If the count is equal to
# the number of vectors, then they all have a value of 1, meaning everything is
# up, else something is down and the node should be taken out of mlab-ns
# rotation. The `== bool 4` ensures that the resulting value will be 0 if the
# count is less than 4.
#
# The final use of `OR` in the queries takes into account where, for some
# reason, node_exporter may not be running on a node, hence the nodeexporter
# metrics will be missing, causing metrics for those nodes to be missing from
# the overall result set. To add these nodes back to the result set we query a
# metric we expect should represent all possible nodes for the experiment, then
# subtract all nodes where up{service="nodeexporter"}==1, leaving us nodes
# where node_exporter is 0 (down).
#
# The use of `min by` in the queries ensures any timeseries added by the final
# `OR` have the exact same label set as the others. In this way, it is a
# built-in sanity check that every timeseries has a consistent set of labels.
QUERIES = {
    'ndt': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="ndt_raw"}) +
            ON (experiment, machine) (script_success{service="ndt_e2e"}) +
            ON (experiment, machine) ((vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="ndt.iupui"} != bool 1)
          ) == bool 4
          OR ON(experiment, machine) up{service="ndt_raw"} == 0
          OR ON(experiment, machine) up{service="ndt_e2e"} == 0
          OR ON(experiment, machine) up{service="ndt_raw"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'ndt_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="ndt_raw_ipv6"}) +
            ON (experiment, machine) (script_success{service="ndt_e2e"}) +
            ON (experiment, machine) ((vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="ndt.iupui"} != bool 1)
          ) == bool 4
          OR ON(experiment, machine) up{service="ndt_raw_ipv6"} == 0
          OR ON(experiment, machine) up{service="ndt_e2e"} == 0
          OR ON(experiment, machine) up{service="ndt_raw_ipv6"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'ndt_ssl': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="ndt_ssl"}) +
            ON (experiment, machine) (script_success{service="ndt_e2e"}) +
            ON (experiment, machine) ((vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="ndt.iupui"} != bool 1)
          ) == bool 4
          OR ON(experiment, machine) up{service="ndt_ssl"} == 0
          OR ON(experiment, machine) up{service="ndt_e2e"} == 0
          OR ON(experiment, machine) up{service="ndt_ssl"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'ndt_ssl_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="ndt_ssl_ipv6"}) +
            ON (experiment, machine) (script_success{service="ndt_e2e"}) +
            ON (experiment, machine) ((vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="ndt.iupui"} != bool 1)
          ) == bool 4
          OR ON(experiment, machine) up{service="ndt_ssl_ipv6"} == 0
          OR ON(experiment, machine) up{service="ndt_e2e"} == 0
          OR ON(experiment, machine) up{service="ndt_ssl_ipv6"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'neubot': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="neubot"}) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="neubot.mlab"} != bool 1)
          ) == bool 2
          OR ON(experiment, machine) up{service="neubot"} == 0
          OR ON(experiment, machine) up{service="neubot"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'neubot_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="neubot_ipv6"}) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="neubot.mlab"} != bool 1)
          ) == bool 2
          OR ON(experiment, machine) up{service="neubot_ipv6"} == 0
          OR ON(experiment, machine) up{service="neubot_ipv6"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'mobiperf': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="mobiperf", instance=~".*:6001"}) +
            ON (experiment, machine)
              (probe_success{service="mobiperf", instance=~".*:6002"}) +
            ON (experiment, machine)
              (probe_success{service="mobiperf", instance=~".*:6003"}) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="1.michigan"} != bool 1)
          ) == bool 4
          OR ON(experiment, machine) up{service="mobiperf"} == 0
          OR ON(experiment, machine) up{service="mobiperf"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
    'mobiperf_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
          (
            (probe_success{service="mobiperf_ipv6", instance=~".*:6001"}) +
            ON (experiment, machine)
              (probe_success{service="mobiperf_ipv6", instance=~".*:6002"}) +
            ON (experiment, machine)
              (probe_success{service="mobiperf_ipv6", instance=~".*:6003"}) +
            ON (experiment, machine)
              (lame_duck_experiment{experiment="1.michigan"} != bool 1)
          ) == bool 4
          OR ON(experiment, machine) up{service="mobiperf_ipv6"} == 0
          OR ON(experiment, machine) up{service="mobiperf_ipv6"}
            UNLESS ON(machine) up{service="nodeexporter"} == 1
        )
        """),
}


class Error(Exception):
    pass


class PrometheusStatusUnparseableError(Error):
    """Indicates that there was an error parsing Prometheus status information."""

    def __init__(self, cause):
        super(PrometheusStatusUnparseableError, self).__init__(cause)


class PrometheusSliceInfo(object):
    """Represents the information necessary to query Prometheus by slice.

    Attributes:
        slice_url: str, URL for querying Prometheus.
        tool_id: str, name of a specific tool.
        address_family: str, formatted string for specifying ipv4 or ipv6.
    """

    def __init__(self, slice_url, tool_id, address_family):
        self._slice_url = slice_url
        self._tool_id = tool_id
        self._address_family = address_family

    def __eq__(self, other):
        return all([self.slice_url == other.slice_url,
                    self.tool_id == other.tool_id,
                    self.address_family == other.address_family])

    def __ne__(self, other):
        return any([self.slice_url != other.slice_url,
                    self.tool_id != other.tool_id,
                    self.address_family != other.address_family])

    @property
    def slice_url(self):
        return self._slice_url

    @property
    def tool_id(self):
        return self._tool_id

    @property
    def address_family(self):
        return self._address_family


def authenticate_prometheus(prometheus):
    """Configures urllib to do HTTP Password authentication for Prometheus URLs.

    Args:
        prometheus: self.PrometheusSliceInfo, authentication information for
        Prometheus.

    Returns:
        A urllib2 OpenerDirector object.
    """
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, prometheus.url, prometheus.username,
                                  prometheus.password)

    authhandler = urllib2.HTTPBasicAuthHandler(password_manager)
    opener = urllib2.build_opener(authhandler)
    return opener


def parse_sliver_tool_status(status):
    """Parses the status of a single sliver tool.

    Args:
        status: dict, status of a sliver tool as returned by Prometheus.

    Returns:
        Tuple of the form (sliver fqdn, current state, extra information)
    """
    # Make sure that the status is minimally correct.
    if not 'value' in status or not 'experiment' in status[
            'metric'] or not 'machine' in status['metric']:
        raise PrometheusStatusUnparseableError(
            'Prometheus status format unrecognized: %s' % status)

    # Joins the experiment name with the machine name to form the FQDN of the
    # experiment.
    sliver_fqdn = status['metric']['experiment'] + '.' + status['metric'][
        'machine']
    # 'status' is a list with two items. The first item ([0]) is a timestamp
    # marking the Prometheus evaluation time. The second, which is the one we
    # want, is the binary status value of the service.
    state = status['value'][1]
    # Prometheus doesn't return any sort of "tool_extra" like baseList.pl does
    # for Nagios, so instead just drop in a note that this was processed from
    # Prometheus data.
    tool_extra = constants.PROMETHEUS_TOOL_EXTRA

    return sliver_fqdn, state, tool_extra


def get_slice_info(prometheus_base_url, tool_id, address_family):
    """Builds a a PrometheusSliceInfo object to query Prometheus for a slice.

    Args:
        prometheus_base_url: str, base URL to get Prometheus slice information.
        tool_id: str, the name of the sliver tool.
        address_family: str, empty for IPv4 or '_ipv6' for IPv6.

    Returns:
         A self.PrometheusSliceInfo object for a slice.
    """
    tool_name = tool_id + address_family
    if not tool_name in QUERIES:
        logging.error('There is no Prometheus query for tool: %s', tool_name)
        return None
    query = urllib.quote_plus(QUERIES[tool_name])
    slice_url = prometheus_base_url + query
    return PrometheusSliceInfo(slice_url, tool_id, address_family)


def get_slice_status(url, opener):
    """Read slice status from Prometheus.

    Args:
        url: str, the API URL for Prometheus for a single tool.
        opener: urllib2.OpenerDirector, opener authenticated with Prometheus.

    Returns:
        A dict mapping sliver fqdn to a dictionary representing the sliver's
        status. For example:

        {
            'foo.mlab1.site1.measurement-lab.org': {
                'status': 'online',
                'tool_extra': 'example tool extra'
            }
        }

        None if Prometheus status is blank or url is inaccessible.
    """
    results = {}
    try:
        raw_data = opener.open(url).read()
    except urllib2.HTTPError:
        logging.error('Cannot open %s.', url)
        return None

    try:
        statuses = json.loads(raw_data)
    except ValueError:
        logging.error('Unable to parse JSON from: %s', url)
        return None

    if statuses['status'] == 'error':
        logging.error('Prometheus returned error "%s" for URL %s.',
                      statuses['error'], url)
        return None

    for status in statuses['data']['result']:
        try:
            sliver_fqdn, state, tool_extra = parse_sliver_tool_status(status)
        except PrometheusStatusUnparseableError as e:
            logging.error('Unable to parse Prometheus sliver status. %s', e)
            continue

        results[sliver_fqdn] = {'tool_extra': tool_extra}
        if state == constants.PROMETHEUS_SERVICE_STATUS_OK:
            results[sliver_fqdn]['status'] = message.STATUS_ONLINE
        else:
            results[sliver_fqdn]['status'] = message.STATUS_OFFLINE

    return results

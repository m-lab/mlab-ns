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
# IMPORTANT NOTE: When querying multiple metrics from the same exporter (e.g.,
# node_exporter), be sure that the label set for each metric is unique. The `OR`
# operator in Prometheus will exclude all metrics but one in the case where they
# have the same label set. For example, in the queries below the vdlimit_* and
# lame_duck_experiment metrics both come from node_exporter. By default, these
# metrics on the same machine will have identical label sets. In this particular
# case, to get around this, we have added unique labels to each metric via the
# scripts that generate the node_exporter metrics files on each node. So, if,
# for example, another blackbox_exporter metric is added (i.e., another
# probe_success), something will need to be done to make sure that the label
# sets are unique for each metric, even if it means using label_replace() in
# these queries.
#
# The label_replace() function is necessary on the gmx_machine_maintenance
# metrics because the GMX has no concept of "experiment", yet this label is
# required for the query, and, more importantly, the output of the query to work
# as intended. label_replace() here just manually adds the experiment label to
# every result with a static value.
QUERIES = {
    'ndt': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="ndt_raw"} OR
            script_success{service="ndt_e2e"} OR
            (vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95 OR
            ((node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"} -
              node_filesystem_free_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) /
                node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) < bool 0.95 OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="ndt.iupui"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "ndt.iupui", "", "") != bool 1
        )
        """),
    'ndt_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="ndt_raw_ipv6"} OR
            script_success{service="ndt_e2e"} OR
            (vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95 OR
            ((node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"} -
              node_filesystem_free_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) /
                node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) < bool 0.95 OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="ndt.iupui"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "ndt.iupui", "", "") != bool 1
        )
        """),
    'ndt_ssl': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="ndt_ssl"} OR
            script_success{service="ndt_e2e"} OR
            (vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95 OR
            ((node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"} -
              node_filesystem_free_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) /
                node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) < bool 0.95 OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="ndt.iupui"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "ndt.iupui", "", "") != bool 1
        )
        """),
    'ndt_ssl_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="ndt_ssl_ipv6"} OR
            script_success{service="ndt_e2e"} OR
            (vdlimit_used{experiment="ndt.iupui"} /
              vdlimit_total{experiment="ndt.iupui"}) < bool 0.95 OR
            ((node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"} -
              node_filesystem_free_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) /
                node_filesystem_size_bytes{cluster="platform-cluster", mountpoint="/cache/data"}) < bool 0.95 OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="ndt.iupui"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "ndt.iupui", "", "") != bool 1
        )
        """),
    'neubot': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="neubot"} OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="neubot.mlab"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "neubot.mlab", "", "") != bool 1
        )
        """),
    'neubot_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="neubot_ipv6"} OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="neubot.mlab"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "neubot.mlab", "", "") != bool 1
        )
        """),
    'mobiperf': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="mobiperf", instance=~".*:6001"} OR
            probe_success{service="mobiperf", instance=~".*:6002"} OR
            probe_success{service="mobiperf", instance=~".*:6003"} OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="1.michigan"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "1.michigan", "", "") != bool 1
        )
        """),
    'mobiperf_ipv6': textwrap.dedent("""\
        min by (experiment, machine) (
            probe_success{service="mobiperf_ipv6", instance=~".*:6001"} OR
            probe_success{service="mobiperf_ipv6", instance=~".*:6002"} OR
            probe_success{service="mobiperf_ipv6", instance=~".*:6003"} OR
            kube_node_spec_taint{cluster="platform-cluster", key="lame-duck"} != bool 1 OR
            lame_duck_experiment{experiment="1.michigan"} != bool 1 OR
            label_replace(gmx_machine_maintenance, "experiment", "1.michigan", "", "") != bool 1
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

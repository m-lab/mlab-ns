import urllib2


def authenticate_nagios(nagios):
    """Configures urllib to do HTTP Password authentication for Nagios URLs.

    Args:
        nagios: object containing nagios auth information
    """
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, nagios.url, nagios.username,
                                  nagios.password)

    authhandler = urllib2.HTTPDigestAuthHandler(password_manager)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)

import pygeoip

def lat_long_by_ipv4(remote_addr):
    gic = pygeoip.GeoIP(
        './mlabns/geo/maxmind/GeoLiteCity.dat',
        pygeoip.constant.STANDARD)
    record = gic.record_by_addr(remote_addr)
    return ','.join([str(record['latitude']), str(record['longitude'])])

def lat_long_by_ipv6(remote_addr6):
    gic = pygeoip.GeoIP(
        './mlabns/geo/maxmind/GeoLiteCityv6.dat',
        pygeoip.constant.STANDARD)
    record = gic.record_by_addr(remote_addr)
    return ','.join([str(record['latitude']), str(record['longitude'])])

def record_by_ipv4(remote_addr):
    gic = pygeoip.GeoIP(
        './mlabns/geo/maxmind/GeoLiteCity.dat',
        pygeoip.constant.STANDARD)
    record = gic.record_by_addr(remote_addr)
    return record

def record_by_ipv6(remote_addr):
    gic = pygeoip.GeoIP(
        './mlabns/geo/maxmind/GeoLiteCityv6.dat',
        pygeoip.constant.STANDARD)
    record = gic.record_by_addr(remote_addr)
    return record


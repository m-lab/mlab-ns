#! /usr/bin/env python

import socket
import argparse
import logging
import sys

GLASNOST_PORT = int(19970)
NPAD_PORT = int(8001)
NDT_PORT = int(3001)
NEUBOT_PORT = int(0)

def check_glasnost_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        data = s.recv(1024)
        logging.info('Recieved: %s (len:%s)', data, len(data))
        if len(data):
            initial_command = data.split(' ')[0]
            if initial_command == 'ip' or initial_command == 'busy':
                return True
            else:
                return False
    except socket.error, (value, message):
        if s:
            s.close()
        logging.error('Failed to check server status: %s', message)
        return False

    if data.split(' ')[0] == 'handshake':
        print 'Handshake successful.'
        return True
    return False

def check_ndt_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.send('2')
        data = s.recv(1024)
        logging.info('Recieved: %s (len:%s)', data, len(data))
    except socket.error, (value, message):
        if s:
            s.close()
        logging.error('Failed to check server status: %s', message)
        return False

    if len(data) == 13:
        print 'Login successful.'
        return True
    return False

def check_npad_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.send('handshake 0\n')
        data = s.recv(1024)
    except socket.error, (value, message):
        if s:
            s.close()
        logging.error('Failed to check server status: %s', message)
        return False

    if data.split(' ')[0] == 'handshake':
        print 'Handshake successful.'
        return True
    return False

def main():
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.INFO)

    ports = {}
    ports['npad'] = NPAD_PORT
    ports['ndt'] = NDT_PORT
    ports['glasnost'] = GLASNOST_PORT
    ports['neubot'] = NEUBOT_PORT

    parser = argparse.ArgumentParser(
        description='Check if the given server is running.')

    parser.add_argument('--host', action="store", dest='host')
    parser.add_argument('--tool', action="store", dest='tool', default='npad')
    parser.add_argument('--port', action="store", dest='port', type=int)

    config = parser.parse_args()

    running = False
    if config.port:
        ports[config.tool] = config.port
    if config.tool == 'npad':
        running = check_npad_server(config.host, ports[config.tool])

    if config.tool == 'ndt':
        running = check_ndt_server(config.host, ports[config.tool])

    if config.tool == 'neubot':
        running = check_neubot_server(config.host, ports[config.tool])

    if config.tool == 'glasnost':
        running = check_glasnost_server(config.host, ports[config.tool])
    if running:
        logging.info(
            'Server %s:%s is running.', config.host, ports[config.tool])
    else:
        logging.info(
            'Server %s:%s is down.', config.host, ports[config.tool])

if __name__ == '__main__':
    main()


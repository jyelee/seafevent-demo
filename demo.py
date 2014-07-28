#/usr/bin/env python
#coding: utf-8

import argparse
import os
import logging
import libevent
import sys
import threading
import Queue

import ccnet
from ccnet.async import AsyncClient
from seaserv import get_repo_owner
from log import LogConfigurator
try:
    import signal
except ImportError:
    import warnings
    warnings.warn('No signals available on this platform, signal tests will be skipped')
    signal = None

CCNET_CONF_DIR = 'CCNET_CONF_DIR'
subscribe_oper = ('seaf_server.event',)

class EventsMQListener(object):

    def __init__(self):
        self._events_queue = Queue.Queue()
        self._seafevents_thread = None
        self._mq_client = None

    def start(self, async_client):
        if self._seafevents_thread is None:
            self._start_worker_thread()

        self._mq_client = async_client.create_master_processor('mq-client')
        self._mq_client.set_callback(self.message_cb)
        self._mq_client.start(*subscribe_oper)
        logging.info('listen to mq: %s', subscribe_oper)

    def message_cb(self, message):
        self._events_queue.put(message)

    def _start_worker_thread(self):
        '''Starts the worker thread for saving events'''
        self._seafevents_thread = SeafEventsThread(self._events_queue)
        self._seafevents_thread.setDaemon(True)
        self._seafevents_thread.start()

class SeafEventsThread(threading.Thread):
    def __init__(self, msg_queue):
        threading.Thread.__init__(self)
        self._msg_queue = msg_queue

    def log_repo_update(self, msg):
        elements = msg.body.split('\t')
        if len(elements) != 3:
            logging.warning("got bad message: %s", elements)
            return

        repo_id = elements[1]
        owner = get_repo_owner(repo_id)

        logging.info('repo: %s was updated by %s' % (repo_id, owner))

    def do_work(self, msg):
        self.log_repo_update(msg)

    def run(self):
        while True:
            msg = self._msg_queue.get()
            self.do_work(msg)

def init_param():
    argu_parser = argparse.ArgumentParser(description='seafevent demo program')
    argu_parser.add_argument('--loglevel',
            default='debug',
            help='log level'
            )

    argu_parser.add_argument(
            '-l',
            '--logfile',
            help='log file'
            )
    return argu_parser

def create_ccnet_session(ccnet_dir, evbase):
    # create ccnet async client
    ccnet_session = AsyncClient(ccnet_dir, evbase)
    try:
        # connect to ccnet server
        ccnet_session.connect_daemon()
        logging.info('connected to ccnet server')
        return ccnet_session
    except ccnet.NetworkError:
        logging.error('can not connect to ccnet server, exit')
        sys.exit() 

def exit_loop(*args):
    logging.info('AsyncClient exit event loop')
    sys.exit(0)


def main():
    argu_parser = init_param()
    args = argu_parser.parse_args()
    logConfig = LogConfigurator(args.loglevel, args.logfile)
    ccnet_dir = None
    if os.environ.has_key(CCNET_CONF_DIR):
        ccnet_dir = os.environ[CCNET_CONF_DIR]
        if not os.path.exists(ccnet_dir):
            logging.error('ccnet directory is not exist, exit')
            sys.exit()
    else:
        logging.error('CCNET_CONF_DIR env variable is not set, exit')
        sys.exit()

    ev_base = libevent.Base()
    async_client = create_ccnet_session(ccnet_dir, ev_base)
    mq_listener = EventsMQListener()
    mq_listener.start(async_client)
    if signal is not None:
        term_sig = libevent.Signal(ev_base, signal.SIGTERM, exit_loop, None)
        term_sig.add()
        term_init = libevent.Signal(ev_base, signal.SIGINT, exit_loop, None)
        term_init.add()
    try:
        async_client.main_loop()
    except ccnet.NetworkError:
        logging.warning('connection to ccnet-server is lost, exit')
        sys.exit()
    except Exception:
        logging.exception('Error in main_loop, exit')
        sys.exit()

if __name__ == '__main__':
    main()

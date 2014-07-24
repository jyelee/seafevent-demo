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
from seafevents.stats.handlers import get_logger, RepoUpdateLogHanlder
from seafevents.log import LogConfigurator

'''
此程序将seafevent监听，处理事件部分抽出，用与展示此流程如何工作。实际上，这部分主要还是依赖Ccnet AsyncClient的MQClientProcessor

1. 创建AsyncClient并与Ccnet Server连接
2. 启动EventsMQListener, 这包括创建MQClientProcessor(它用来监听我们所需要的事件，如程序中的subscribe_oper中的事件字符串)并向其注册回调函数(即当有事件到来时，如何处理。程序中是将事件放入阻塞队列中以供工作线程来处理)，创建并启动工作线程(工作线程会循环查看阻塞队列来获取消息并处理。本demo中仅仅演示了监听资料库更改事件，并将更改信息记录log操作。)
3. AsyncClient进入事件循环
'''


subscribe_oper = ('seaf_server.event', 'seahub.stats')

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

    def do_work(self, msg):
        RepoUpdateLogHanlder(None, msg)

    def run(self):
        while True:
            msg = self._msg_queue.get()
            self.do_work(msg)

def init_param():
    argu_parser = argparse.ArgumentParser(description='seafevent demo program')
    argu_parser.add_argument('ccnet_dir', 
            help='ccnet config directory'
            )
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


def main():
    argu_parser = init_param()
    args = argu_parser.parse_args()
    if not os.path.exists(args.ccnet_dir):
        logging.error('ccnet directory is not exist, exit')
        sys.exit()
    logConfig = LogConfigurator(args.loglevel, args.logfile)
    async_client = create_ccnet_session(args.ccnet_dir, libevent.Base())
    mq_listener = EventsMQListener()
    mq_listener.start(async_client)
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

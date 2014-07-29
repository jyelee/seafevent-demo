seafevent-demo
==============

Seafile server will broadcast some messages such as repo update and put block event sended by seafile and file direcotry download file view event sended by seahub. Sometimes, maybe you want to use these messages to do some meaningfull things such as monitor, so the demo will shows how to receive these messages.

The demo is used to log information of repo update event.

1. Make sure Ccnet Server has been started.
2. Create AsyncClient instance and connect with Ccnet Server.
3. As receive message operation is handled by MqClientProc, we need to create MqClientProc instance and from the instance subscribe event source such as seaf_server.event subscribed in demo. In the demo, using EventsMQListener to encapsulate above operation and create a worker thread to mointer message queue, if there is a message the worker thread will log related information.
4. AsyncClient instance start event loop.

Message format

If you subscribe perferred message, you will get follow formatted message:
```
class Message(object):
    def __init__(self, d):
        self.flags = int(d['flags'])    // Message flag, value is 0
        self.from_ = d['from']          // ID of sender
        self.to = d['to']               // ID of receiver
        self.id = d['id']               // UUID
        self.ctime = float(d['ctime'])  // Send timestamp
        self.rtime = float(d['rtime'])  // Receive timestamp, value is 0
        self.app = d['app']             // Message type, for seafile value is seaf_server.event, for seahub value is seahub.stats
        self.body = d['body']           // Message content, it's format is operation\t...\t....\t..., such as for repo-update it's content is repo-update\trepo_id\tcommit_id
```
Run demo

**Note:** seafevent uses libevent python binding module, you must install [it](https://github.com/haiwen/python-libevent) in your environment.

1. Based on your environment modify run.sh 
2. Execute run.sh

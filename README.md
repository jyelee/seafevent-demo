seafevent-demo
==============

The demo is show how to use seafevent to listen event of seafile and seahub

此demo将seafevent监听，处理事件部分抽出，用与展示此流程如何工作。实际上，这部分主要还是依赖Ccnet AsyncClient的MQClientProcessor

1. 创建AsyncClient并与Ccnet Server连接
2. 启动EventsMQListener, 这包括创建MQClientProcessor(它用来监听我们所需要的事件，如程序中的subscribe_oper中的事件字符串)并向其注册回调函数(即当有事件到来时，如何处理。程序中是将事件放入阻塞队列中以供工作线程来处理)，创建并启动工作线程(工作线程会循环查看阻塞队列来获取消息并处理。本demo中仅仅演示了监听资料库更改事件，并将更改信息记录log操作。)
3. AsyncClient进入事件循环

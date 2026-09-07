# HUNDSUN票据交易管理平台软件V5.0-接口开发指导

HUNDSUN票据交易管理平台软件V5.0-接口开发手册

# 消息通道开发

消息通道旨在与外部系统进行通讯。目前adapter已实现tcp、http、ibm mq三种常见的通讯方式。更多通讯方式，由产品部持续开发集成更新。为了向前兼容，启动新版消息通道必须开启配置中心参数adapter.is_use_new_message_channel=1

启用消息通道

在application.properties文件中，配置spring.profiles.active项，例如：spring.profiles.active=tcp即启用tcp通讯方式，spring.profiles.active=tcp,http即同时启用tcp和http通讯方式

配置消息通道

不同的通讯方式涉及的配置项也各不相同。

2.2.1 tcp通讯配置

2.2.2 http通讯方式

2.2.3 ibm mq通讯方式

# 消息转换开发

消息转换是为了将内部消息转换程外部系统所识别报文，以及将外部消息转换成内部所识别消息。接口类MessageConverter的toMessage方法(内部json转换成外部消息)和fromMessag方法(外部消息转换成内部json)。

消息转换采用约定优于配置规则，即：接口编号+MessageConverter则为java类名，同时也是spring bean的名字，如图所示：

3.1 接出消息转换

接出消息转换除处理转换消息外，还有一个重要职责，即指定该接口所路由的消息通道。

继承AbstractMessageRequestReplyConverter重写toMessage、 fromMessag以及getDestination(指定该接口接出消息通道)方法。目前adapter提供三个已实现指定消息通道的接出消息转换，分别为AbstractJmsMessageRequestReplyConverter、AbstractTcpMessageRequestReplyConverter、AbstractHttpMessageRequestReplyConverter，若是接出通讯方式是tcp、http、mq，则只需要按照实际消息通讯方式，选择继承即可。

3.2 接入消息

接出消息转换除处理转换消息外，还有一个重要职责，即指定外部接口服务与内部服务映射关系。继承AbstractMessageApplyResponseConverter重写toMessage、 fromMessag以及getFunctionIdMapping(外部服务码与内部功能号映射关系)，规则为：外部服务码从起始至末尾前，内部功能号在数组末尾，如图所示：

由于接入消息外部服务码无法统一识别，因此需要继承AbstractMessageInterceptor实现preInvoke方法，通过preInvoke来对外部消息进行拦截处理，获取外部服务码，并同时设定内部功能号。同时需要在注解@Component下在加一行注解@Primary，如图所示：

同时也可以重写postInvoke方法来对响应消息进行后置处理(此步骤非必须)。

由于接入消息处理时会出现异常，因此需要继承AbstractExceptionHandler重写handleFailure方法，通过handleFailure方法来返回通用失败消息。同时需要在注解@Component下在加一行注解@Primary，如图所示：


### 表格


| #外部系统tcp服务端ip adapter.tcp.client.host_name=127.0.0.1 #外部系统tcp服务端port adapter.tcp.client.port=9088 #adapter tcp监听端口 adapter.tcp.server.port=9088 #是否启用netty日志功能 adapter.tcp.netty_log_enable=true |
| --- |


### 表格


| #外部系统http/https服务端ip adapter.http.client.host_name=127.0.0.1 #外部系统http/https服务端port adapter.http.client.port=8099 #外部系统http/https服务端uri adapter.http.client.uri=/bemp-adapter/test/message #调用外部系统http/https请求内容类型 adapter.http.client.content_type=application/json #调用外部系统http/https请求是否压缩内容 adapter.http.client.content_compressor=false #调用外部系统是否启用https协议 adapter.http.client.ssl_enable=false #外部系统https请求key alias adapter.http.client.ssl_key_alias=CLIENT_ROOT #外部系统https请求key store文件 adapter.http.client.ssl_key_store=E:/https.jks #外部系统https请求key store类型  adapter.http.client.ssl_key_store_type=JKS #外部系统https请求trust store类型  adapter.http.client.ssl_trust_store_type=JKS #外部系统https请求trust store文件 adapter.http.client.ssl_trust_store=E:/https.jks #外部系统https请求key store密钥 adapter.http.client.ssl_key_store_password=123abc #外部系统https请求trust store密钥 adapter.http.client.ssl_trust_store_password=123abc #是否启用netty日志功能 adapter.http.netty_log_enable=true #adapter http/https监听端口 adapter.http.server.port=9087 #adapter http/https上下文路径 adapter.http.server.context_path=/adapter #adapter接收http/https请求是否开启内容压缩 adapter.http.server.content_compressor=false #adapter是否启用https协议 adapter.http.server.ssl_enable=false #adapter启用https key store路径 adapter.http.server.ssl_key_store=E:/https.jks #adapter启用https trust store路径 adapter.http.server.ssl_trust_store=E:/https.jks #adapter启用https key store密钥 adapter.http.server.ssl_key_password=123abc #adapter启用https trust store密钥 adapter.http.server.ssl_trust_password=123abc #adapter接收http/https请求内容类型 adapter.http.server.content_type=application/json |
| --- |


### 表格


| #ibm mq ip和port adapter.mq.connection_name_list=192.168.56.101(1417),192.168.56.102(1417) #ibm mq消息传输方式 adapter.mq.transport_type=1 #ibm mq字符集标识，819用于unix，1381用于window adapter.mq.ccsid=819 #ibm mq队列管理器 adapter.mq.queue_manager=QMEMBFE #ibm mq通道 adapter.mq.queue_channel=SYSTEM.AUTO.SVRCONN #接出请求队列 adapter.mq.send_out_queue=3143010006_3 #接出响应队列 adapter.mq.send_in_queue=3143010006_5 #接入响应队列 adapter.mq.recv_out_queue=3143010006_5 #接入请求队列 adapter.mq.recv_in_queue=3143010006_3 #连接是否启用权限认证 adapter.mq.user_credentials=true #ibm mq用户名 adapter.mq.username=mqm #ibm mq密码 adapter.mq.password=mqm |
| --- |

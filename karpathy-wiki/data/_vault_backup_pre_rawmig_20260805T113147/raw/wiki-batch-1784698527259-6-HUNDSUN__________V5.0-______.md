# HUNDSUN票据交易管理平台软件V5.0-后端开发手册

HUNDSUN电子商业汇票综合处理平台软件V5.0-开发手册

# 背景

本文为开发人员提供参考，同时达到规范开发的目的。

# 个性化需求开发说明

分层结构图：

## 功能开发

前端：负责向操作员提供数据展示、操作交互功能。HUI是基于vue.js的前端框架，具

有容易上手，使用也更简单；速度响应快等特点。提供了UI组件模式，用户可以方便的编写UI组件，并发布到应用当中。在frontend工程，创建个性化页面路径src/views/bizViews/banks/xxbank/一级模块编号/二级模块编号/，页面开发具体详见

控制层，负责接收操作人员的操作请求及操作数据，将传递到业务服务层进行处理，同时向操作人员应答处理结果，工程命名：xxbank-biz-ar，包路径

com.hundsun.bemp.xxbank.biz，示例如下：

说明：所有的控制层必须继承基类BaseController，@RestController()注解代表当前类为控制器；@RequestMapping("/ecds/ecdsBasicData")注解代表前端访问URL，

@RequestMapping(value = "/queryEcdsCommonData", method = { RequestMethod.POST, RequestMethod.GET })注解代表前端可以通过get和post请求方式访问的方法

服务层包括：业务服务、公共服务、基础服务三类服务。

业务服务：即满足业务办理需求的业务功能

公共服务：供业务服务复用的功能，偏业务类。

基础服务：供业务服务、公共服务复用的功能，偏技术类、平台类。

原子功能，服务内容的逻辑单元、一般业务服务的实现由多个原子功能组件，通过原子层组合出完成的业务服务。这样使得功能逻辑更为清晰，使用更为简单。

如果服务功能本身比较简单，则可以没有原子层

创建服务工程：xxbank-biz-as，接口工程：xxbank-biz-api

包路径：com.hundsun.bemp.xxbank.biz

示例接口：

说明：@CloudService注解代表发布服务

接口实现类

说明：@CloudComponent注解代表定义bean,@Resource代表依赖注入，调用DAO层方法

创建DTO

数据访问层：

提供对数据库及缓存的操作。

数据库访问集成Mybatis开源组件

缓存采用Redis缓存中间件

工程中src\test\resources\codegen添加generator.xml，Intellij IDEA开发工具执行命令

mvn mybatis-generator:generater自动生成pojo：

com.hundsun.bemp.shcpe.ecds.dao.EcdsCommonDataDao

和映射文件：com/hundsun/bemp/shcpe/ecds/dao/EcdsCommonDataDao.xml

添加Dao层类

说明：基类已经有基本的增删改查方法。

## 功能改造

### 前端传参改造

前端向后台增加传参，如果DTO中已经有预留字段直接放入预留字段即可，如果没有可以将业务请求DTO继承产品定义的BaseDto，里面包含三个预留字段。

### 数据库字段保存改造

如果需要将个性化的字段保存到数据库中，目前各个业务模块表已经添加预留字段，如果超过三个字段，可以将多个字段转换成json数据或者逗号分隔等方式保存。

### 服务层、原子层和DAO层方法改造

新建java类，继承原产品部的java类

如public class XxbankBookServiceImpl extends DemoBookServiceImpl {

新的java类上添加 @CustomizedBean注解。表示是个性化扩展的功能，将替换产品部提供的功能代码。

如下：

重写父类的功能方法

如果要复用原方法，可以调用super.get(req)，如果需要改造原方法，可以将原方法内容拷贝过来在此基础上改造。

新的java类注册为spring的bean

注册为bean有多种方法：

不需要发布jres服务，添加@Service或其他spring的注解。如

发布为jres微服务，

加@CloudComponent，发布为微服务。

注意，发布微服务时，一定要加“implements DemoBookService”，即使父类已经实现接口。

# Apapter开发说明

接出示图：bemp做为客户端

接入示图：bemp做为服务方

## 产品接口开发

adapter（通讯适配）模块工程下图：

### Bemp调用外部系统(client方)

#### 接口定义

一般的，bemp调用外部系统，接口应该是外部系统提供。但是，为了屏蔽不同客户的接口不一致问题。所以产品需要定义一个通用的适配接口，以适应不同的外部接口。

在工程bemp-adapter-client-api中定义接口编号：定义一个XXOpCode常量类：如下图样例所示,

在工程bemp-adapter-client-api中定义入参BaseRequest的泛型类Dto

产品功能模块依赖bemp-adapter-client-api工程:

在产品功能里面组装请求参数类BaseRequest，BaseRequest调用api方法

#### 路由配置

路由配置分三层:全局配置、模块配置、功能点配置,

所有的配置文件统一放置在：

served\conf\src\main\resources\adapter\clientroute

全局的路由配置

在_global.rootclientroute.xml文件中 < ClientRoute/>节点内配置

一般不需要调整

模块的路由配置

在_global.rootclientroute.xml文件中 <Module/>节点内配置

功能点的路由配置：xxx.clientroute.xml文件，命名规范：模块名+.clientroute.xml

具体配置说明：

以上三种配置文件中属性说明：

配置生效原则，功能点配置 > 模块配置 > 全局配置，举例说明：请求通道reqChannel未在xxx.clientroute.xml中ClientField定义，则判断是否在模块配置Module中是否已定义，如果还是没有继续在全局路由中ClientRoute 寻找如果还是没有使用默认请求通道outReqChannel。

#### 扩展实现

自定义请求通道，需要实现接口ServiceReqChannel

自定义转换器，目前只提供的json，如果有个性化的具体在

自定义连接通道

### 外部系统调用bemp(server方)

#### 路由到内部功能

在/bemp-conf工程的/resources/adapter/serviceroute目录下进行配置

文件名:xxx. serviceroute.xml

配置项：

moduleName : 该交易号没有配置必需配置项时,去配置模块名寻找配置

opCode :交易号,接口唯一标识

serverConverter :转换器,接受的外系统数据转换为本系统服务参数

functionId :服务编号

#### 定义功能接口

示例：

## 个性化接口开发

当产品不能满足对接需求，由项目组个性化开发，创建适配模块(xxbank为项目名称)，

xxbank-adapter-api：适配器接口工程

xxbank-adapter-as：适配器服务工程，pom.xml依赖

xxbank-conf：个性化配置工程

### bemp调用外部系统(client方)

请求通道请求报文转换连接通道应答报文转换，个性化开发可以调整四步中任意一步，如果需要自定义参考产品开发客户端的扩展实现。

xxbank-conf工程增加个性化的路由配置文件名xxx.ext.clientroute.xml，路径：src\main\resources\adapter\clientroute\

如:

配置生效原则：

个性化功能点配置 > 产品功能点配置 >个性化模块配置 > 产品模块配置 >个性化全局配置 > 产品全局配置

如果产品中和项目中都对opCode="m10005"进行配置，以项目中配置优先

### 外部系统调用bemp(server方)

xxbank-conf工程配置个性化的服务路由文件：文件名格式*.ext.serviceroute.xml，路径：src\main\resources\adapter\serviceroute\，functionId开发个性化的微服务

# 部署

## 配置参数（配置中心）

根据实际需要的通讯机制配置如下参数

票据系统作为客户端

Webservice请求

连接外围webservice的地址：adapter.wsoutchannel_wsdl_address

连接外围webservice的方法名：adapter.wsoutchannel_operation

连接外围webservice的命名空间：adapter.wsoutchannel_namespace_uri

Socket请求

连接的socket的ip：adapter.socket_client_ip

连接的socket的超时时间：adapter.socket_client_timeout

http请求

作为客户端，连接服务端的地址：adapter.http_client_address

http://127.0.0.1:port/services/services/HttpConnectInChannel，port为应用启动端口。

票据系统作为服务端

发布ws标准接口，标准json格式webservice服务发布配置

是否开启webservice服务端：adapter.is_open_webservice_server=1

adapter.webservice_base_address=http://127.0.0.1:8090/services/WsConnectInChannel

访问地址：http://127.0.0.1:8090/services/WsConnectInChannel?wsdl

Socket服务

是否开启socket服务端：adapter.is_open_socket_server

发布端口配置：adapter.socket_server_port

连接的socket的端口：adapter.socket_client_port

## 打包发布

新增工程xxbank-adapter，pom.xml添加如下配置，打包发布成war包进行部署即可


### 表格


| public class BaseDto  implements Serializable { 	private static final long serialVersionUID = 1988052246401885570L; 	 	private String reserve1;//保留字段。个性化开发使用，产品部代码逻辑不使用。 	private String reserve2;//保留字段。个性化开发使用，产品部代码逻辑不使用。 	private String reserve3;//保留字段。个性化开发使用，产品部代码逻辑不使用。 |
| --- |


### 表格


| transplant_flag | 移植标识（空为非移植票，非空为移植票） | varchar2(64) | × | × |  |
| --- | --- | --- | --- | --- | --- |
| reserve1 | 保留字段1 | varchar2(250) | × | × |  |
| reserve2 | 保留字段2 | varchar2(250) | × | × |  |
| reserve3 | 保留字段3 | varchar2(250) | × | × |  |
| create_time | 创建时间 | number(17,0) | × | × |  |
| update_time | 修改时间 | number(17,0) | × | × |  |


### 表格


| @CustomizedBean public class XxbankBookServiceImpl extends DemoBookServiceImpl { |
| --- |


### 表格


| @Override 	public RoomDto get(BaseRequest<Long> req) { 		RoomDto  dto = super.get(req); 		dto.setRoomName("xxbank_"+dto.getRoomName());		 		return dto; 	} |
| --- |


### 表格


| @Service @CustomizedBean public class XxbankBookAtomImpl extends DemoBookAtomImpl  implements DemoBookAtom{ |
| --- |


### 表格


| @CustomizedBean @CloudComponent public class XxbankBookServiceImpl extends DemoBookServiceImpl implements DemoBookService{ { |
| --- |


### 表格


| <dependency>     <groupId>com.hundsun.bemp</groupId>     <artifactId>bemp-adapter-client-api</artifactId>     <version>${project.version}</version>     <scope>compile</scope> </dependency> <dependency>     <groupId>com.hundsun.bemp</groupId>     <artifactId>bemp-adapter-api</artifactId>     <version>${project.version}</version>     <scope>compile</scope> </dependency> |
| --- |


### 表格


| CommonResp commonResp = MsgClientUtil.send(new BaseRequest<>(...)); |
| --- |


### 表格


| <ClientRoute reqChannel="jresReqChannel"              clientConverter="msgJsonClientConverter"              connectChannel="wsConnectOutChannel"> ... </ClientRoute> |
| --- |


### 表格


| <?xml version="1.0" encoding="UTF-8"?> <ClientRoute reqChannel="jresReqChannel"              clientConverter="msgJsonClientConverter"              connectChannel="wsConnectOutChannel">      <Module moduleName="bm"             reqChannel="jresReqChannel"> </Module> ... </ClientRoute> |
| --- |


### 表格


| <?xml version="1.0" encoding="UTF-8"?> <ClientRoute moduleName="bm">      <!--企业同业黑名单通知-->     <ClientField opCode="POBM010303"                  reqChannel="outReqChannel"                  mockReqChannel="blackRollInfoReqChannel"                  clientConverter="msgJsonClientConverter"                  connectChannel="wsConnectOutChannel" /> ... </ClientRoute> |
| --- |


### 表格


| 属性 | 是否必输 | 默认(beanId) | 说明 |
| --- | --- | --- | --- |
| opCode | 是 | 无 | 交易号,接口唯一标识 |
| reqChannel | 否 | outReqChannel | 请求通道,可选(outReqChannel[调用外系统通道],noneReqChannel[挡板通道,不执行调用],jresReqChannel[jres请求通道,调用bemp系统的jres微服务]) |
| mockReqChannel | 否 | noneReqChannel | 挡板通道,开启挡板时读取的请求通道,如果参数req_channel_mock_mode为all，并且reqChannel 不是jresReqChannel，则请求通道为mock通道；mock_opcode_+opcode为1，请求通道为mock通道， 如果为0不走mock通道，如果没有配置继续判断mock_opcode_defvalue为0不走mock，否则全部走mock |
| clientConverter | 否 | msgJsonClientConverter | 转换器,转换为与外部传输的格式 |
| connectChannel | 否 | wsConnectOutChannel | 连接通道,连接外系统执行调用 |
| replyPojoPath | 否 | com.hundsun.bemp.fw.common.pojo.CommonResp中retData默认类型Object，且为空 | 将com.hundsun.bemp.fw.common.pojo.CommonResp中retData转换为具体的类 |
| timeout | 否 |  | 调用超时时间 |


### 表格


| <?xml version="1.0" encoding="UTF-8"?> <ServiceRoute moduleName="bm">      <!--查询电票签约账号信息-->     <ServiceField opCode="PICE070118"                     serverConverter="msgJsonServerConverter"                     functionId="PICE070118">     </ServiceField>   </ServiceRoute> |
| --- |

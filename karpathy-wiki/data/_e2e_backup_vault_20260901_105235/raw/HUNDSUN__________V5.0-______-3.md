# HUNDSUN票据交易管理平台软件V5.0-服务接口规范

更改履历

注：更改人除形成初稿，以后每次修改在未批准确认前均需采用修订的方式进行修改。

目录

第1章	引言	4

1.1	目的	4

1.2	使用范围	4

1.3	规范原则	4

第2章	编程约定	5

2.1.	接口名称命名规约	5

2.2.	接口编号命名规约	5

2.3.	接口校验规约	6

2.4.	接口发布规范	6

引言

## 目的

通过此文档，提供一套标准BEMP对外发布服务接口规范，使各开发人员生产的代码有更好的一致性，并提高开发团队的生产效率。

## 使用范围

本规范适用于票据5.0项目，并最终作为项目评审与验收依据。

## 规范原则

1)	遵循业界标准

2)	可读性强，意义清楚

3)	整洁严谨、风格统一

编程规范

接口名称命名规范

命名规约遵守“HUNDSUN票据交易管理平台软件V5.0-JAVA开发规范”。如：

1）【强制】 代码中的命名均不能以下划线或美元符号开始，也不能以下划线或美元符号结束。 反例： _name/__name/$Object/name_/name$/Object$/user_name

2）【强制】 代码中的命名严禁使用拼音与英文混合的方式，更不允许直接使用中文的方式。 说明：正确的英文拼写和语法可以让阅读者易于理解，避免歧义。注意，即使纯拼音命名方式也要避免采用。 反例： DaZhePromotion [打折] / getPingfenByName() [评分] / int 某变量 = 3 正例： hundsun / taobao / youku / hangzhou 等国际通用的名称，可视同英文。

3）【强制】类名使用UpperCamelCase风格，必须遵从驼峰形式，但以下情形例外：（领域模型的相关命名）DO / BO / DTO / VO等。 正例：MarcoPolo / UserDO / XmlService / TcpUdpDeal / TaPromotion 反例：macroPolo / UserDo / XMLService / TCPUDPDeal / TAPromotion

4）【强制】方法名、参数名、成员变量、局部变量都统一使用lowerCamelCase风格，必须遵从驼峰形式。 正例： localValue / getHttpMessage() / inputUserId

接口编号命名规范

1.  接口编号规则：是否产品接口（一位）+方向（一位）+一级模块（两位字母）+二级模块（两位数字）+API类编号(两位数字）+方法编号(两位数字）=8位：

第一位：P 表示产品，B表示个性化

第二位：I 表示我方为server方， O表示我方为client方。

模块编号，请参见模块划分章节

产品的接口样例：

如：PISM010101、POPC010303。

个性化的接口样例：

如：BISM010101、BOPC010303

接口参数规范

请求报文格式

普通请求

通用报文头信息

入参DTO规范

格式:

带分页请求

请求分页对象

格式:

单个ID值请求

格式:

单个字符串请求

格式:

应答报文格式

retCode为"000000"表示成功；否则为失败

成功应答报文

格式:

样例一（普通对象）：

格式:

样例一（列表）：

格式:

样例二（带分页）：

格式:

失败应答报文

格式:

参数字段规范

数据类型规范

通用字段规范

注：其它字段参照票据元数据。

接口校验规约

非空判断（null-valid）：如：提示“{xxx}不能为空”

例子：利率（rate） 提示：利率不能为空

字段长度判断（length-valid）：如：提示“{xxx}长度不能超过{xxx}位”

例子：出票人账号（drwrAcctNo） 提示：出票人账号长度不能超过32位

定字段长度判断（length-valid）：如：提示“XXX必须{XXX}位

例子：承兑人开户行号（acptBankNo） 提示：承兑人开户行号必须12位数字

金额判断（num-accuracy-valid）：如：提示“xxx金额格式：最多16位整数,2位小数"

例子：票面金额（billMoney） 提示：票面金额格式：最多16位整数,2位小数

枚举判断（enum-valid）：如：提示“xxx:取值非法，正确的取值范围：[xxx]"

例子：票据类型（billType） 提示：票据类型:取值非法，正确的取值范围：[AC01，AC02]

比较值判断（cmp-valid）：如：提示“xxx大于xxx "

例子：

最大票据金额（maxBillMoney）: 最大票据金额（maxBillMoney） 提示：最大票据金额大于最小票据金额

数字判断（num-valid）：如：提示“xxx只能为数字串"

例子：出票日期（remitDt） 提示：出票日期只能为数字串

自定义判断（individualization-valid）：如：

BbepValidUtil.validBusiDate(applyDate) ;提示："申请日期不是当前营业日期"

增加通用校验规则

日期（校验长度，数字类型，合法性）

行号（只校验数字或长度）

机构号（校验非空）

金额（校验最多16位整数,2位小数）等

接口校验 例子：

<valid-field>

<service interface-name="XXXX.XXXXXXService" method-name="XXXX"></service>

<null-valid>

memberNo:"法人编号为空";

</null-valid>

<length-valid>

memberNo(6-6):"法人编号必须为6位";

</length-valid>

<num-valid>

branchCode:"应答机构代码只能为数字串";

</num-valid>

<enum-valid>

signUpMarkCode:"SU00,SU01";

</enum-valid>

</valid-field>

接口发布规范

1.接口注解@CloudService注解用于服务生产者声明微服务。该注解声明位于服务接口类上。

2．实现注解@CloudComponent注解用于服务生产者声明微服务实现。该注解声明位于服务实现类上。该注解不带任何属性。

修订记录规范

修改说明，规范：（序号+[操作]+接口名称（接口编号） +  具体说明）

规则：操作说明：[A]-增加；[M]-修改；[D]-删除；

接口文档版本规范

接口文件中版本号与POM版本号保持一致。

每个版本接口文档，增加版本号命名的文件夹存放。


### 表格


| 版本号 | 修改编号 | 更改时间 | 更改的 图表和章节 | 更改简要描述 | 更改人 | 批准人 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |


### 表格


| 字段名称 | 字段 | 数据类型 | 数据长度 | 必输项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 交易码 | opCode | String | 30 | Y |  |
| 版本号 | version | String | 10 | Y |  |
| 交易流水 | reqFlowNo | String | 32 | Y |  |
| 渠道号 | channelNo | String | 10 | Y |  |
| 法人编号 | reqLegalNo | String | 30 | N |  |
| 操作员号 | reqUserNo | String | 30 | N | 上传实际发起本次操作员，自动任务使用虚拟柜员 |
| 机构号 | reqBrchNo | String | 30 | N |  |
| 备注1 |  | String | 250 | N |  |
| 备注2 |  | String | 250 | N |  |
| 备注3 |  | String | 250 | N |  |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 | 备注 |
| --- | --- | --- | --- | --- |
| 报文头信息 |  | Header |  |  |
| 请求报文 | requestDto |  | [1..1] |  |
| --客户号 | custNo | Max50Char | [1..1] |  |
| --客户名称 | custName | Max255Text | [1..1] |  |


### 表格


| {      "opCode": "PISM010101", 	"channelNo": "pjsy", 	"reqFlowNo": "2020061100001", 	" reqUserNo ": "admin", 	"version": "1.0.0"， 	"requestDto": { 		"custNo": "001" "custName": "恒生电子001" 	}	 } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 | 备注 |
| --- | --- | --- | --- | --- |
| 报文头信息 |  | Header |  |  |
| 分页信息 | pageInfo |  |  |  |
| --当前页码 | pageNo | Max10NumericText | [1..1] |  |
| --页面大小 | pageSize | Max6NumericText | [1..1] |  |
| 请求报文 | requestDto |  | [1..1] |  |
| --客户号 | custNo | Max50Char | [1..1] |  |
| --客户名称 | custName | Max255Text | [1..1] |  |


### 表格


| {     "opCode": "PISM010102", 	"channelNo": "pjsy", 	"reqFlowNo": "2020061100001", 	"opCode": "1001", "userNo": "admin", 	"version": "1.0.0" 	"pageInfo": {		 		"pageNo": 1, 		"pageSize": 10 	}, 	"requestDto": { 		" custNo ": "001", 		" custName ": "恒生电子001" 	}, } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 | 备注 |
| --- | --- | --- | --- | --- |
| 报文头信息 |  | Header |  |  |
| 请求报文 | id |  | [1..1] |  |


### 表格


| {      "opCode": " PISM010103", 	"channelNo": "pjsy", 	"reqFlowNo": "2020061100001", 	"userNo": "admin", 	"version": "1.0.0"， 	"id":100001 } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 | 备注 |
| --- | --- | --- | --- | --- |
| 报文头信息 |  | Header |  |  |
| 请求报文 | code |  | [1..1] |  |


### 表格


| {      "opCode": " PISM010104", 	"channelNo": "pjsy", 	"reqFlowNo": "2020061100001", 	"userNo": "admin", 	"version": "1.0.0"， "code":"99010001" } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 |
| --- | --- | --- | --- |
| 返回码 | retCode | Max50Char | [1..1] |
| 返回信息 | retMsg | Max250Char | [1..1] |
| 返回对象 | retData |  | [0..n] |


### 表格


| {   "retCode": "000000",   "retMsg": "success", "retData": {jsonData} } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 |
| --- | --- | --- | --- |
| 返回码 | retCode | Max50Char | [1..1] |
| 返回信息 | retMsg | Max250Char | [1..1] |
| 返回对象 | retData |  | [0..n] |
| --客户号 | custNo | Max50Char | [1..1] |
| --客户名称 | custName | Max255Text | [1..1] |


### 表格


| { "retCode": "000000", "retMsg": "success", "retData": { 		   " custNo ": "001", 		   " custName ": "恒生电子001" 	} } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 |
| --- | --- | --- | --- |
| 返回码 | retCode | Max50Char | [1..1] |
| 返回信息 | retMsg | Max250Char | [1..1] |
| 返回对象 | retData |  | [0..1] |
| --列表数据 | list |  | [0..n] |
| ----客户号 | custNo | Max50Char | [1..1] |
| ----客户名称 | custName | Max255Text | [1..1] |


### 表格


| { "retCode": "000000", "retMsg": "success", "retData": [ 			{ 		         " custNo ": "001", 		         " custName ": "恒生电子001" 			}, 			{ 				  " custNo ": "002", 		          " custName ": "恒生电子002" 				} 			  ] } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 |
| --- | --- | --- | --- |
| 返回码 | retCode | String(50) | [1..1] |
| 返回信息 | retMsg | String(250) | [1..1] |
| 返回对象 | retData |  | [1..1] |
| --分页信息 | pageInfo |  | [0..n] |
| ----总记录数 | count |  | [1..1] |
| ----当前页 | pageNo |  | [1..1] |
| ----页大小 | pageSize |  | [1..1] |
| ----总页数 | pageCount |  | [1..1] |
| --列表数据 | list |  | [0..n] |
| ----客户号 | custNo | Max50Text | [1..1] |
| ----客户名称 | custName | Max255Text | [1..1] |


### 表格


| { "retCode": "000000", "retMsg": "success", "retData": {"list":[ 				{ 				  " custNo ": "001", 				  " custName ": "恒生001" 				}, 				{ 				  " custNo ": "002", 				  " custName ": "恒生002" 				} 			  ], 			"pageInfo": { 				"count": 90, 				"pageCount": 9, 				"pageNo": 1, 				"pageSize": 10 			  } 			} } |
| --- |


### 表格


| 参数名称 | 参数英文名 | 数据类型 | 属性 | 备注 |
| --- | --- | --- | --- | --- |
| 返回码 | retCode | String(50) | [1..1] | 000000-成功 |
| 返回信息 | retMsg | String(250) | [1..1] |  |


### 表格


| {   "retCode": "000002",   "retMsg": "发生异常!" } |
| --- |


### 表格


| 数据类型 | 数据定义 | 附加说明 |
| --- | --- | --- |
| MaxMin30NumericText | 固定30位数字 |  |
| DraftTypeCode | 2位字母+2位数字编码 | AC01银承 AC02商承 |
| CDMedia | 2位字母+2位数字编码 | ME01 纸票 ME02 电票 |
| SerialNo | 50位字符串 | 只含a-z,A-Z,0-9，不含中文和其它符号 |
| PrcStatCode | 1位字母 | S-成功 Z-处理中 F-处理失败 |
| OpType | 2位字母+2位数字编码 | OP01-新增 OP02-修改 OP03-删除 |
| BankMarkCode | 12数字 | 取值范围[0,9] |
| RepurchasedMarkCode | 2位字母+2位数字编码 | RM00买断式 RM01回购式 |
| CurrencyCode | 固定填写CNY |  |
| CurrencyAndAmount | (便签里面3位英文币种属性)金额总长19位（含小数点），最多16位整数,2位小数 | 币种属性固定填写“CNY” |
| PercentageRate | 7位数字，小数部分6位 | 用来表示百分比的单位 例如，0.123表示12.3% |
| MaxxxxNumericText | 表示数字串，最少1位，最多xxx位的数字。 |  |
| MaxMinxxxNumericText | 表示固定XXX字节的字符串,只含0-9 | 取值范围[0,9] |
| MaxxxxAlphaNumericText | 表示字符串,最少1位，最多XXX位,只含a-z,A-Z,0-9 | 不含中文和其它符号 |
| MaxMinxxxAlphaNumericText | 表示固定XXX字节的字符串,只含a-z,A-Z,0-9 | 不含中文和其它符号 |
| MaxxxxText | 表示字符串，最少1字符，最多xxx字符的文本，含数字、字母、中文、及其他各种字符。 | 每个数字、字母、中文及其他各种字符均占一个字符。 |
| MaxMinxxxText | 表示固定XXX字节的字符串,只含数字、字母、中文、及其他各种字符。 |  |
| BanEndorsementMarkCode | 2位字母+2位数字编码 | EM00可再转让 EM01不得转让 |
| SettlementMarkCode | 2位字母+2位数字编码 | SM00线上清算  SM01线下清算 |
| CreditRatings | 3位数字、字母、“+”或“-” |  |
| SignUpMarkCode | 2位字母+2位数字编码 | SU00同意签收 SU01拒绝签收 |
| Flag | 1位数字 | 1是 0否 |
| DishonorCode | 2位字母+2位数字编码 | DC00、与自己有直接债权债务关系的持票人未履行约定义务； DC01、持票人以欺诈、偷盗或者胁迫等手段取得票据； DC02、持票人明知有欺诈、偷盗或者胁迫等情形，出于恶意取得票据； DC03、持票人明知债务人与出票人或者持票人的前手之间存在抗辩事由而取得票据； DC04、持票人因重大过失取得不符合《票据法》规定的票据； DC05、超过提示付款期； DC06、被法院冻结或收到法院止付通知书； DC07、票据未到期； DC08、商业承兑汇票承兑人账户余额不足。 DC09、其他（必须注明）。 |
| DraftOriginCode | 1位数字 | 1-网银 2-信贷 |
| DataOrigCode | 2位字母+2位数字编码 | DO01-前端录入 DO02-人行转发 DO03-渠道录入 |
| CmonCd | a-z,A-Z,0-9或“-”号，最短1位，最长10位文本 | 格式为八位数字或字母加一横杠加校验码，例如“12345678-X”，所有报文中的组织机构代码均按此格式填写 |
| SocCode | a-z,A-Z,0-9或“-”号，最短1位，最长10位文本 | 格式为八位数字或字母加一横杠加校验码，例如“12345678-X”，所有报文中的组织机构代码均按此格式填写 |
| RoleCode | 2位字母+2位数字编码 | RC00接入行 RC01企业 RC02人民银行 RC03被代理行 RC04被代理财务公司 RC05接入财务公司 |
| SignTypeCode | 2位字母+2位数字编码 | ST00签约 ST01续约 ST02解约 |
| SignProdKindCode | 2位字母+2位数字编码 | SK00电票签约 SK01票据池签约 SK02一键签票 SK03线上贴现 SK04代客提示付款 SK05代客扣款 SK06代客签收 |
| FeeKindCode | 2位字母+2位数字编码 | FK01按票面金额收费 FK02按交易笔数收费 FK03按时间收费 |
| AppointStatCode | 2位字母+2位数字编码 | AS01预约成功 AS02预约失败 AS03预约成功处理成功 AS04预约成功处理失败 |
| RateTypeCode | 2位字母+2位数字编码 | 360--年利率 30--月利率 1--日利率 |
| AcptTypeCode | 2位字母+2位数字编码 | AT01本行签发 AT02他行代我行签发 AT03我行代他行签发 AT04行内新开机构代理签发 AT05普通行内代理签发 |
| DiscTypeCode | 2位字母+2位数字编码 | DT01买断式 DT02赎回式 DT03商票保贴 |
| DraftProdCode | 6位数字 |  |
| PayTypeCode | 2位字母+2位数字编码 | PT01买方付息 PT02卖方付息 PT03协议付息 PT04第三方付息 PT05卖方与第三方付息 PT06买方与第三方付息 PT07买方、卖方、第三方付息 |
| GuarModeCode | 2位字母+2位数字编码 | GM01普通担保 GM02票据池担保 GM03存单质押担保 |
| ImpawnTypeCode | 2位字母+2位数字编码 | IT01普通质押 IT02入池质押 |
| EApplyQueryType | 2位字母+2位数字编码 | QT00-可签收查询 QT01-撤销申请查询 QT02-可签收查询汇总 QT03-可撤销查询汇总 |
| LegalPersonNo | 10位字符串 | 只含a-z,A-Z,0-9，不含中文和其它符号 |
| BusiTypeCode | 2位数字 | 01-承兑 02-贴现 03-托收 04-质押 05-质押解除 |
| ChangeMode | 1位数字 | 1-使用 2-作废 |
| PaperBillNo | 16位数字 |  |
| OpMode | 2位字母+2位数字编码 | OM01-批次操作 OM02-明细操作 |
| ApprovalCode | 2位字母+2位数字编码 | AC01-通过 AC02-驳回 |
| CmonCd | 10位字符串 | a-z,A-Z,0-9或“-”号，最短1位，最长10位文本 |
| MaxxxxChar | 只含a-z,A-Z,0-9,或'-' | 不含中文，和‘-’以外的符号 |
| RecourseTypeCode | 2位字母+2位数字编码 | RT00拒付追索  RT01非拒付追索 |
| RecourseReasonCode | 2位字母+2位数字编码 | RC00承兑人被依法宣告破产   RC01承兑人因违法被责令终止活动 |
| AssignModeTypeCode | 2位字母+2位数字编码 | AM01-手动   AM02-自动 |
| CertTypeCode | 2位字母+2位数字编码 | CTO1-身份证 CT02-组织机构代码 CT03-统一社会信用代码 |
| SuspendTypeCode | 2位字母+2位数字编码 | ST00口头挂失 ST01正式挂失 |
| SuspendOpTypeCode | 2位字母+2位数字编码 | SO01 挂失 SO02 解挂 |
| SuspendStatCode | 2位字母+2位数字编码 | SS00 未挂失 SS01 已挂失 |
| BackOpenTypeCode | 2位字母+2位数字编码 | BO01登记 BO02未用退回 BO03未用退回复合 |
| AgcyRgstOperTypeCode | 2位字母+2位数字编码 | AR01-登记   AR02-撤销登记 |
| RgstOperTypeCode | 2位字母+2位数字编码 | RT01-退票入库   RT02-退票结清 |
| ChangeVochTypeCode | 2位字母+2位数字编码 | CV01-使用   CV02-作废 |
| PartnerTypeCode | 2位字母+2位数字编码 | PT01-企业   PT02-同业 |
| RgstTypeCode | 2位字母+2位数字编码 | 2位字母+2位数字编码 |
| AcptStatCode | 2位字母+2位数字编码 | AS0X-已作废 AS00-签发 AS01-承兑 AS02-未用退回 AS03-足额扣款 AS04-垫款 AS05-付款 AS06-部分扣款 |
| AutoTypeCode | 2位字母+2位数字编码 | AT00-无自动化 AT01-自动出票登记 AT02-出票登记-提示承兑 AT03-出票登记-提示收票 AT04-出票登记-提示承兑-提示收票 AT05-提示承兑 AT06-提示承兑-提示收票 AT07-提示收票 |
| DiscStyleCode | 2位字母+2位数字编码 | DS00-普通贴现 DS01-自助贴现 |
| ProxyPropositionCode | 2位字母+2位数字编码 | PP00-开户机构代理申请签章 PP01-票据当事人自己签章 |
| BillOperCode | 2位字母+2位数字编码 | OC00-新增票据 OC01-修改票据 OC02-删除票据 |
| HldrQueryTypeCode | 3位字母+2位数字编码 | HQT00-根据持有人查询 HQT01-根据权利人查询 HQT02-查询持有人及权利人 |
| BusiTypeCode | 2位数字编码 | 01-承兑 02-贴现 03-托收 04-质押 05-质押解除 |
| LockBillTypeCode | 1位数字编码 | 1：锁定 2：解锁 |
| ErrorTypeCode | 2位字母+2位数字编码 | ET00--根据批次，存在锁票失败，则直接抛错，锁票记录回滚 ET01--根据明细，存在锁票失败，捕获异常，返回错误明细，锁票记录不回滚 ET02--根据明细，存在锁票失败，抛出异常，锁票记录回滚 |
| RiskTypeCode | 2位字母+2位数字编码 | RS00--非风险票据 RS01--挂失止付 RS02--公示催告 RS03--司法冻结 RS04--争议票据 RS05--除权判决 |


### 表格


| 报文要素 | 参数英文名 | 数据类型 | 说明 |
| --- | --- | --- | --- |
| 票据类型 | billType | DraftTypeCode | AC01银承 AC02商承 |
| 票据介质 | billClass | CDMedia | ME01 纸票 ME02 电票 |
| 出票日期 | remitDt | MaxMin8NumericText | 固定8位数字 |
| 汇票到期日 | dueDt | MaxMin8NumericText | 固定8位数字 |
| 票面金额 | billMoney | CurrencyAndAmount | (便签里面3位英文币种属性)金额总长19位（含小数点），最多16位整数,2位小数 币种属性固定填写“CNY” |
| 出票人全称 | drwrName | Max60Text | 表示字符串，最少1字符，最多xxx字符的文本，含数字、字母、中文、及其他各种字符。 每个数字、字母、中文及其他各种字符均占一个字符。 |
| 出票人账号 | drwrAcctNo | Max32Char | 最长32位 |
| 出票人开户行名 | drwrBankName | Max60Text |  |
| 出票人开户行号 | drwrBankNo | MaxMin12NumericText | 固定12位数字 |
| 收款人全称 | pyeeName | Max60Text |  |
| 收款人账号 | pyeeAcctNo | Max32Char |  |
| 收款人开户行名 | pyeeBankName | Max60Text |  |
| 收款人开户行号 | pyeeBankNo | MaxMin12NumericText | 固定12位数字 |
| 承兑人全称 | acptName | Max60Text |  |
| 承兑人账号 | acptAcctNo | Max32Char |  |
| 承兑人开户行名 | acptBankName | Max60Text |  |
| 承兑人开户行号 | acptBankNo | MaxMin12NumericText | 固定12位数字 |
| 票据来源 | dataOrig | DataOrigCode |  |
| 单笔票据请求流水 | txlFlowNo | MaxMin18NumericText | 固定18位数字 |
| 承兑协议编号 | acptProtocalNo | Max60Text |  |
| 贴现利率 | discRate | PercentageRate | 7位数字，小数部分6位 用来表示百分比的单位 例如，0.123表示12.3% |

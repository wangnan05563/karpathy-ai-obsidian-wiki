**中国票据业务系统直连接口规范
【ECDS迁移票据业务分册】**

上海票据交易所

2026年6月

文档修订记录

|  |  |  |  |
| --- | --- | --- | --- |
| **版本编号** | **变化状态** | **简要说明** | **日期** |
| V1.0 | A | 新建 | 2024-3-15 |
| V1.1 | M | 修改，见修改记录 | 2024-5-29 |
| V1.4 | - | - | 2026-06-01 |

*注：变化状态：A—增加，M—修改，D—删除*

**目 录**

[修改记录 5](#_Toc998226236)

[说明 6](#_Toc1853456747)

[1 各业务场景报文流程 7](#_Toc2006413140)

[1.1 逾期提示付款 7](#_Toc661187943)

[1.2 追索 7](#_Toc659900027)

[1.2.1 追索通知 7](#_Toc859429248)

[1.2.2 追索同意清偿 8](#_Toc1212425308)

[1.2.3 追索通知清分失败 8](#_Toc245241466)

[1.3 业务撤销 9](#_Toc2133142048)

[1.4 通用通知 9](#_Toc325609157)

[2 报文数据定义 9](#_Toc1048798099)

[2.1 迁移业务报文清单 9](#_Toc1802654145)

[2.2 数据类型 10](#_Toc2142441048)

[2.3 迁移票据状态 12](#_Toc1648716205)

[2.4 迁移业务转换规则 13](#_Toc718291328)

[2.4.1 迁移时承接与代理规则 13](#_Toc1830600602)

[2.4.2 迁移后承接与代理规则 13](#_Toc133078276)

[2.5 机构参与者代码与报文头发起人、接收人填写规则 13](#_Toc704983887)

[2.6 迁移票据业务报文组件 13](#_Toc1566208042)

[2.6.1 迁移票据参与者信息组件 13](#_Toc901116651)

[2.6.2 迁移票据业务信息组件 14](#_Toc1789905077)

[2.6.3 迁移票据业务应答组件 14](#_Toc173879350)

[2.6.4 迁移票据状态信息组件 15](#_Toc2119778671)

[2.6.5 迁移票据通知信息组件 15](#_Toc1482968366)

[2.6.6 迁移票据基本信息组件 15](#_Toc272763553)

[2.6.7 迁移票据历史详细信息组件 15](#_Toc875764795)

[3 票据业务系统报文（XML格式） 28](#_Toc912556196)

[3.1 迁移票据业务申请报文（MCP.001.001） 28](#_Toc1811189233)

[3.1.1 报文功能 28](#_Toc86273651)

[3.1.2 报文结构 28](#_Toc1537192950)

[3.1.3 报文说明 30](#_Toc1909268533)

[3.1.4 报文处理规则 30](#_Toc1084499887)

[3.2 迁移票据业务撤销报文（MCP.002.001） 31](#_Toc1243166049)

[3.2.1 报文功能 31](#_Toc1768198025)

[3.2.2 报文结构 31](#_Toc1745687830)

[3.2.3 报文说明 32](#_Toc1903066076)

[3.2.4 报文处理规则 32](#_Toc480143625)

[3.3 迁移票据业务转发报文（MCP.003.001） 33](#_Toc810629490)

[3.3.1 报文功能 33](#_Toc823894)

[3.3.2 报文结构 33](#_Toc465802026)

[3.3.3 报文说明 34](#_Toc1136238647)

[3.3.4 报文处理规则 34](#_Toc1049621993)

[3.4 迁移票据业务应答报文（MCP.004.001） 34](#_Toc120972523)

[3.4.1 报文功能 34](#_Toc1131196047)

[3.4.2 报文结构 34](#_Toc550854551)

[3.4.3 报文说明 35](#_Toc839263851)

[3.4.4 报文处理规则 35](#_Toc814313002)

[3.5 迁移票据业务通知报文（MCP.005.001） 36](#_Toc683932827)

[3.5.1 报文功能 36](#_Toc1544247738)

[3.5.2 报文结构 36](#_Toc233037396)

[3.5.3 报文说明 37](#_Toc1585049478)

[3.5.4 报文处理规则 37](#_Toc1186669167)

[4 附录（迁移票据业务通知范围） 38](#_Toc406916746)

[4.1 业务触发通知场景 38](#_Toc1557344501)

[4.2 应急变更触发通知场景 39](#_Toc522153886)

[5 迁移票据存量在途业务信息供数格式标准 40](#_Toc679680300)

[5.1 编写目的 40](#_Toc285625649)

[5.2 字符集 40](#_Toc1434710082)

[5.3 数据文件说明 40](#_Toc343385885)

[5.4 迁移票据存量在途业务信息文件 40](#_Toc371899300)

[5.4.1 文件名 40](#_Toc824419384)

[5.4.2 文件内容 40](#_Toc105170770)

[5.4.3 文件获取方式 40](#_Toc1456399187)

[5.4.4 文件格式 40](#_Toc2067585433)

# **修改记录**

|  |  |  |
| --- | --- | --- |
| **序号** | **修改日期** | **修改说明** |
| 1 | 2024-5-29 | M:补充迁移票据历史详细信息组件中贴现信息的<AOAccnInf>为<AOAccnInf/>；  M:补充迁移票据历史详细信息组件中贴现信息的<DscntBk/>属性为[1..1]；  M:补充迁移票据历史详细信息组件中质押解除信息的<Dt>为<Dt/>；  M:补充迁移票据历史详细信息组件中提示付款信息<Prsnttn/>属性为[1..1]；  M:补充迁移票据历史详细信息组件中提示付款信息的<DshnrCd/>数据类型为为EcdsDishonorCode；  M:修改迁移票据历史详细信息组件中迁移后票据历史行为信息中业务申请人信息的<BrId/>属性为[0..1]，并增加备注描述；  M:修改迁移票据历史详细信息组件中迁移后票据历史行为信息中业务应答人信息的<BrId/>属性为[0..1]，并增加备注描述；  M:修改MCP.005.001报文中持票人信息的<BrId/>属性为[0..1]，并增加备注描述； |

**说明：**[C]-创建；[M]-修改；[A]-增加；[D]-删除；

**说明**

为了推进电子商业汇票系统（以下简称ECDS）数据迁移工作的实施，上海票据交易所根据数据迁移工作方案，并结合市场参与者的实际需求和意见编写了本分册，对迁移中各业务场景报文流程、报文数据定义、报文格式规范等规则予以明确。

本分册的适用场景为ECDS存量未结清票据在数据迁移后的到期后业务办理，其中涉及到的相关术语整理如下：

迁移票据：ECDS中所有到期未结清、未作废、未失效的，在迁移时点一次性全部迁移至票据业务系统迁移模块中的票据；

直连模式：会员机构开通了迁移票据业务申请报文、迁移票据业务撤销报文、迁移票据业务转发报文、迁移票据业务应答报文、迁移票据业务通知报文等5个直连报文权限的业务处理模式；

客户端模式：会员机构仅开通迁移票据业务通知报文直连报文权限的业务处理模式。

# **各业务场景报文流程**

## **逾期提示付款**

![](data:image/x-emf;base64...)

## **追索**

### **追索通知**

![](data:image/x-emf;base64...)

说明：

在被追索人发起追索同意清偿申请前，追索人可继续向其他被追索人发起追索通知。

### **追索同意清偿**

![](data:image/x-emf;base64...)

说明：

1、被追索人1发起追索同意清偿申请后，其余被追索人不可发起追索同意清偿申请。

2、若追索人拒绝被追索人1的追索同意清偿申请，则其余被追索人可以继续发起追索同意清偿申请。

### **追索通知清分失败**

![](data:image/x-emf;base64...)

## **业务撤销**

![](data:image/x-emf;base64...)

## **通用通知**

![](data:image/x-emf;base64...)

说明：

1. 会员采取客户端模式的，业务发生时通过该报文通知其业务变化。
2. 票交所触发持票人变更或撤销时通过该报文通知其业务发生变化。
3. 持票人通过客户端自行申请下发业务通知。

具体通知范围见附录（迁移票据业务通知范围）

# **报文数据定义**

## **迁移业务报文清单**

|  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **报文编号** | **报文名称** | **报文方向** | **适用的会员类型** | **是否新增报文** | **是否加签** | **是否加密** | **是否对账** | **报文时序** |
| MCP.001.001 | 迁移票据业务申请报文 | 参与者->票交所 | B,F,I | 是 | 是 | 是 | 是 | 00 |
| MCP.002.001 | 迁移票据业务撤销报文 | 参与者<->票交所 | B,F,I | 是 | 是 | 是 | 是 | 00 |
| MCP.003.001 | 迁移票据业务转发报文 | 参与者<-票交所 | B,F,I | 是 | 是 | 是 | 是 | 00、01 |
| MCP.004.001 | 迁移票据业务应答报文 | 参与者<->票交所 | B,F,I | 是 | 是 | 是 | 是 | 00 |
| MCP.005.001 | 迁移票据业务通知报文 | 参与者<-票交所 | B,F,I | 是 | 是 | 是 | 是 | 00、01 |
| CIM.001.002 | 通用业务确认报文 | 参与者<-票交所 | B,F,I,R,E | 否 | 否 | 否 | 否 | 00、01 |

注：1、适用的会员类型包括B.银行，F.财务公司，I.其他，R.供应链平台，E.直连B2B平台。

2、报文时序与登记托管子系统业务时序一致。

## **数据类型**

以下数据类型使用范围仅限于本分册。

|  |  |  |
| --- | --- | --- |
| 类型名称 | 类型定义 | 附加说明 |
| MaxxxxText | 表示字符串，最少1字符，最多xxx字符的文本，含数字、字母、中文、及其他各种字符。 | 每个数字、字母、中文及其他各种字符均占一个字符。 |
| MaxxxxNumericText | 表示数字串，最少1位，最多xxx位的数字。 |  |
| MaxMinxxxNumericText | 表示固定xxx位长度的数字串。 |  |
| MaxxxxAlphaNumericText | 表示字符串，最少1字节，最多xxx字节的文本，只含a-z,A-Z,0-9。 | 不含中文和其它符号 |
| MaxMinxxxAlphaNumericText | 表示固定xxx字节的字符串，只含a-z,A-Z,0-9。 | 不含中文和其它符号 |
| ISODateTime | yyyy-mm-ddTHH:MM:SS | 例如：2007-03-11T15:09:05，其中的"T"为日期和时间的分割符，是必须的 |
| ISODate | yyyy-mm-dd | 例如：2007-03-09 |
| PercentageRate | 7位数字，小数部分6位 | 用来表示百分比的单位  例如，0.534表示53.4% |
| CurrencyAndAmount | (便签里面3位英文币种属性)金额总长19位（含小数点），最多16位整数,2位小数 | 币种属性固定填写“CNY” |
| BanEndorsementMarkCode | 2位字母+2位数字编码 | EM00 可再转让  EM01 不得转让 |
| SignUpMarkCode | 2位字母+2位数字编码 | SU00 同意  SU01 拒绝  SU02 清分失败 |
| DraftTypeCode | 2位字母+2位数字编码 | AC01 银票/财票  AC02 商票 |
| RoleCode | 2位字母+2位数字编码 | RC00接入行  RC01企业  RC02人民银行  RC03被代理行  RC04被代理财务公司  RC05接入财务公司 |
| CmonCd | a-z,A-Z,0-9或“-”号，最短1位，最长10位文本 | 格式为八位数字或字母加一横杠加校验码，例如“12345678-X”，所有报文中的组织机构代码均按此格式填写 |
| ConsignmentCode | 2位字母+2位数字编码 | CC00 含委托/承诺兑付  CC01 不含委托/不承诺兑付 |
| ProxySignatureCode | 2位字母+2位数字编码 | PS00 开户机构代理回复签章  PS01 票据当事人自己签章 |
| RepurchasedMarkCode | 2位字母+2位数字编码 | RM00买断式  RM01回购式 |
| SettlementMarkCode | 2位字母+2位数字编码 | SM00 线上清算  SM01 线下清算 |
| RecourseTypeCode | 2位字母+2位数字编码 | RT00拒付追索  RT01非拒付追索 |
| EcdsDishonorCode | 2位字母+2位数字编码 | DC00 与自己有直接债权债务关系的持票人未履行约定义务；  DC01 持票人以欺诈、偷盗或者胁迫等手段取得票据；  DC02 持票人明知有欺诈、偷盗或者胁迫等情形，出于恶意取得票据；  DC03 持票人明知债务人与出票人或者持票人的前手之间存在抗辩事由而取得票据；  DC04 持票人因重大过失取得不符合《票据法》规定的票据；  DC05 超过提示付款期；  DC06 被法院冻结或收到法院止付通知书；  DC07 票据未到期；  DC08 商业承兑汇票承兑人账户余额不足。  DC09 其他（必须注明）。 |
| RecourseReasonCode | 2位字母+2位数字编码 | RC00 承兑人被依法宣告破产  RC01 承兑人因违法被责令终止活动 |
| CreditRatings | 3位数字、字母、“+”或“-” |  |
| ProxyPropositionCode | 2位字母+2位数字编码 | PP00 开户机构代理申请签章  PP01 票据当事人自己签章 |
| MCPBusiCategory | 2位字母+2位数字编码 | MC01 迁移票据逾期提示付款申请  MC02 迁移票据追索通知  MC03 迁移票据追索同意清偿申请 |
| MCPEndorTp | 2位字母+2位数字编码 | MT01 逾期提示付款  MT02 追索 |
| ExceptionCode | 2位字母+2位数字编码 | EC00－无此账号  EC01－无此行号  EC02－名称不符  EC03－贴现入账信息账号错误 |
| MCPBusiScenariosCode | 2位字母+4位数字编码 | MP0501-逾期提示付款申请  MP0502-逾期提示付款申请撤销  MP0503-逾期提示付款应答同意  MP0504-逾期提示付款应答拒绝  MP0505-追索通知发起  MP0506-追索通知应答清分失败  MP0507-追索通知撤销  MP0508-追索同意清偿申请  MP0509-追索同意清偿申请撤销  MP0510-追索同意清偿应答同意（未结清）  MP0511-追索同意清偿应答同意（结清）  MP0512-追索同意清偿应答拒绝  MP0513-原交易系统转迁移模块追索  MP0514-原交易系统票据结清  MP0515-应急撤销  MP0516-持票人变更（未结清）-非同意清偿待签收状态  MP0517-持票人变更（未结清）-同意清偿待签收状态  MP0518-持票人变更（结清）-非同意清偿待签收状态  MP0519-持票人变更（结清）-同意清偿待签收状态  MP0520-已逾票据业务办理时限  具体见分册附录4表格中“场景编码”。 |

## **迁移票据状态**

|  |  |  |
| --- | --- | --- |
| **序号** | **迁移票据状态名称** | **状态码** |
|  | 背书待签收 | 100001 |
|  | 买断式贴现待签收 | 110101 |
|  | 买断式贴现已签收 | 110106 |
|  | 回购式贴现待签收 | 110201 |
|  | 质押待签收 | 180001 |
|  | 保证待签收 | 170001 |
|  | 提示付款待签收 | 200001 |
|  | 逾期提示付款待签收 | 210001 |
|  | 提示收票已签收 | 030006 |
|  | 背书已签收 | 100006 |
|  | 回购式贴现赎回已签收 | 120006 |
|  | 质押已至票据到期日 | 180020 |
|  | 质押解除已签收 | 190006 |
|  | 提示付款已拒付（不可进行拒付追索） | 200512 |
|  | 提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 200312 |
|  | 提示付款已拒付（可拒付追索，可以追所有人） | 200412 |
|  | 逾期提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 210312 |
|  | 逾期提示付款已拒付（可拒付追索，可以追所有人） | 210412 |
|  | 拒付追索待清偿 | 220607 |
|  | 拒付追索同意清偿待签收 | 230601 |
|  | 拒付追索同意清偿已签收 | 230606 |
|  | 非拒付追索待清偿 | 220707 |
|  | 非拒付追索同意清偿待签收 | 230701 |
|  | 非拒付追索同意清偿已签收 | 230706 |
|  | 非拒付追索已撤销 | 220710 |
|  | 已逾票据业务办理时限 | 000026 |
|  | 票据已结清 | 000000 |

## **迁移业务转换规则**

### **迁移时承接与代理规则**

迁移时，承接与代理转换关系为：

（1）当行为人非代理的,行号在ECDS未设置承接关系，则根据该行号在票据业务系统中确定有效机构代码。

（2）当行为人非代理的,行号在ECDS已设置承接关系的，则保留ECDS承接关系，根据承接行行号在票据业务系统中确定有效机构代码。

（3）当行为人为代理的[RC03（被代理行）或者RC04（被代理财务公司）]，则根据被代理机构的代理行号和代理账号信息在票据业务系统中确定被代理机构代码信息，同时，迁移票据参与者信息组件中行为人行号填写为被代理机构代码对应的行号信息，机构参与者代码填写被代理机构代码信息。（**具体可见2.6.1章节**）

（4）根据上述规则未找到有效机构的，可联系票交所处理。

### **迁移后承接与代理规则**

迁移后业务，ECDS承接关系不再维护，对迁移时确定的机构代码根据票据业务系统承接关系进行更新维护。

## **机构参与者代码与报文头发起人、接收人填写规则**

1. 报文体中业务申请人机构参与者代码所属业务办理渠道与报文头中报文发起人一致。
2. 报文体中业务接收人机构参与者代码所属业务办理渠道与报文头中报文接收人一致。

## **迁移票据业务报文组件**

### **迁移票据参与者信息组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 名称 | <Nm/> | [1..1] | Max60Text |  |
|  | 组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | 银行账户信息 | <Acct/> | [1..1] |  |  |
|  | --账号 | <Id/> | [1..1] | Max32AlphaNumericText | 如参与者为接入行或接入财务公司，填写一个‘0’；如为人民银行的，也填写一个‘0’；其他情况下，填写业务行为人账号 |
|  | --开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText | 填写原ECDS业务信息中的**原始开户行行号；若为代理，则填写被代理行行号** |
|  | 机构参与者代码 | <BrId/> | [1..1] | MaxMin9NumericText | 根据开户行行号，结合ECDS承接关系和票据业务系统承接关系，填写**最终业务办理机构参与者代码**。具体见组件说明。 |

说明：

1. 开户行行号：填写原ECDS业务信息中的原始开户行行号；若为代理，则填写被代理机构行号。
2. 机构参与者代码：为迁移时根据开户行行号确定的机构代码；该机构参与者代码随票据业务系统承接关系维护而改变；业务办理时须填写最新机构参与者代码（若有承接关系则填写承接机构参与者代码）。

例如：

1. ECDS中业务信息开户行行号为A，并在ECDS中已设置承接行行号为B；
2. 在票据业务系统中开户行行号B对应的有效机构参与者代码为C；
3. 迁移后，按照2.4.1所描述规则，确定开户行行号A在票据业务系统中机构参与者代码为C；迁移票据参与者信息组件中开户行行号填写A，机构参与者代码填写C；若票据业务系统中参与者机构代码为C被承接给参与者机构D，则承接后该业务参与者信息组件中开户行行号填写A，机构参与者代码填写D。

### **迁移票据业务信息组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 申请日期 | <Dt/> | [1..1] | ISODate | 当前系统工作日期 |
|  | 业务种类 | <BusiCategory/> | [1..1] | MCPBusiCategory | MC01 迁移票据逾期提示付款申请  MC02 迁移票据追索通知  MC03 迁移票据追索同意清偿申请 |
|  | 追索类型 | <Tp/> | [0..1] | RecourseTypeCode | 业务种类为MC02 迁移票据追索通知时必填；其他情况不填。 |
|  | 业务金额 | <Amt/> | [1..1] | CurrencyAndAmount | 提示付款金额需等于票面金额，其余不做校验 |
|  | 追索理由代码 | <RcrsRsnCd/> | [0..1] | RecourseReasonCode | 当追索类型为非拒付追索时必填，当追索类型为拒付追索时可填，其他情况下不填 |
|  | 备注 | <Note/> | [0..1] | Max500Text | 可填写逾期提示付款原因、追索原因、业务备注信息等。  注：当业务种类为MC01 迁移票据逾期提示付款申请时，须填写逾期原因说明。 |
|  | 代理申请标识 | <PrxyPropstn/> | [0..1] | ProxyPropositionCode | 迁移票据逾期提示付款申请时必填；  其他业务申请不填。 |
|  | 电子签名 | <ElctrncSgntr/> | [1..1] | Max4000Text |  |

### **迁移票据业务应答组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 应答日期 | <Dt/> | [1..1] | ISODate |  |
|  | 应答标识 | <SgnUpMk/> | [1..1] | SignUpMarkCode |  |
|  | 拒付理由代码 | <DshnrCd/> | [0..1] | EcdsDishonorCode | 当应答标识为拒绝且业务种类为迁移票据逾期提示付款申请时必填，否则不填 |
|  | 备注 | <Note/> | [0..1] | Max500Text | 1.业务备注信息。 2.应答标识为清分失败时，须填写ExceptionCode代码。  3.拒付理由代码为DC09时，必填。 |
|  | 代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode | 迁移票据逾期提示付款应答允许代理回复标识为“银行代理”或“客户自己签章”，其他场景必须为“客户自己签章” |
|  | 电子签名 | <ElctrncSgntr/> | [1..1] | Max4000Text |  |

### **迁移票据状态信息组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 迁移票据状态 | <CdStatus/> | [1..1] | MaxMin6AlphaNumericText | 见2.3章节 |

### **迁移票据通知信息组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 通知信息 | <DrftStsAltrnInf/> | [1..1] |  |  |
|  | --通知日期 | <Dt/> | [1..1] | ISODate | 当前系统工作日期 |
|  | --场景编码 | <BusiScnarsCode> | [0..1] | MCPBusiScenariosCode |  |
|  | --通知内容 | <Note/> | [0..1] | Max300Text |  |

### **迁移票据基本信息组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 票据基本信息 | <DraftBasicInf/> | [1..1] |  |  |
|  | --票据号码 | <CdNo/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <CdAmt/> | [1..1] | CurrencyAndAmount |  |

### **迁移票据历史详细信息组件**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 迁移票据历史信息 | <MigrationDrftHisInfo/> |  |  |  |
|  | --迁移前票据历史行为信息 | <ComrclDrft/> | [1..1] |  | 按票据行为发生顺序排列 |
|  | --迁移后票据历史行为信息 | <HistoryInf/> | [0..n] |  | 按票据行为发生顺序排列 |

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| 迁移前票据历史行为信息<ComrclDrft/> | | | | | |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | --票据种类 | <Tp/> | [1..1] | DraftTypeCode |  |
|  | --电子票据号码 | <IdNb/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <IsseAmt/> | [1..1] | CurrencyAndAmount |  |
|  | --出票日期 | <IsseDt/> | [1..1] | ISODate |  |
|  | --到期日 | <DueDt/> | [1..1] | ISODate |  |
|  | --不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode | EM00可再转让 EM01不得转让 |
|  | --备注 | <Rmrk/> | [0..1] | Max256Text |  |
|  | --出票人信息 | <Drwr/> | [1..1] |  |  |
|  | ----类别 | <Role/> | [1..1] | RoleCode |  |
|  | ----名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ----组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ----账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ----开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ----信用等级 | <CdtRatgs/> | [0..1] | CreditRatings |  |
|  | ----评级机构 | <CdtRatgAgcy/> | [0..1] | Max60Text |  |
|  | ----评级到期日 | <CdtRatgDueDt/> | [0..1] | ISODate |  |
|  | --承兑人信息 | <Accptr/> | [1..1] |  |  |
|  | ----名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ----账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ----开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | --收款人信息 | <Pyee/> | [1..1] |  |  |
|  | ----名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ----账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ----开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | --票据历史行为信息 | <ComrclDrftBiz/> | [0..n] |  |  |
|  |  |  |  |  |  |
|  | 承兑 | <ComrclDrftBiz/> |  |  |  |
|  | --承兑信息 | <Accptnc/> | [1..1] |  |  |
|  | ----提示承兑签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----到期无条件支付委托 | <UcondlConsgnmtMrk/> | [1..1] | ConsignmentCode |  |
|  | ----到期无条件支付承诺 | <UcondlPrmsMrk/> | [1..1] | ConsignmentCode |  |
|  | ----交易合同编号 | <TxlCtrctNb/> | [0..1] | Max30Text |  |
|  | ----发票号码 | <InvcNb/> | [0..1] | Max30Text |  |
|  | ----承兑协议编号 | <AccptncAgrmtNb/> | [0..1] | Max30Text |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----出票人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----承兑人信息 | <Accptr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------信用等级 | <CdtRatgs/> | [0..1] | CreditRatings |  |
|  | ------承兑人备注 | <CdtRatgAgcy/> | [0..1] | Max60Text | **对应原来的承兑人评级机构内容。** |
|  | ------评级到期日 | <CdtRatgDueDt/> | [0..1] | ISODate |  |
|  | ----出票人信息 | <Drwr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 收票 | <ComrclDrftBiz/> |  |  |  |
|  | --收票信息 | <Issnc/> | [1..1] |  |  |
|  | ----提示收票签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----出票人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr /> | [0..1] | Max256Text |  |
|  | ----收款人信息 | <Pyee/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ----出票人信息 | <Drwr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 背书 | <ComrclDrftBiz/> |  |  |  |
|  | --背书信息 | <Endrsmt/> | [1..1] |  |  |
|  | ----背书签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----背书人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----背书人信息 | <Endrsr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----被背书人信息 | <Endrsee/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 贴现 | <ComrclDrftBiz/> |  |  |  |
|  | --贴现信息 | <Dscnt/> | [1..1] |  |  |
|  | ----贴现种类 | <RpdMk/> | [1..1] | RepurchasedMarkCode |  |
|  | ----贴现签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----贴现利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----贴现实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----贴现赎回开放日 | <RpdOpenDt/> | [0..1] | ISODate |  |
|  | ----贴现赎回截止日 | <RpdDueDt/> | [0..1] | ISODate |  |
|  | ----贴现赎回利率 | <RpdIntrstRate/> | [0..1] | PercentageRate |  |
|  | ----贴现赎回金额 | <RpdAmt/> | [0..1] | CurrencyAndAmount |  |
|  | ----交易合同编号 | <TxlCtrctNb/> | [0..1] | Max30Text |  |
|  | ----发票号码 | <InvcNb/> | [0..1] | Max30Text |  |
|  | ----贴现协议编号 | <DscntAgrmtNb/> | [0..1] | Max30Text |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----贴出人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----入账信息 | <AOAccnInf/> | [1..1] |  |  |
|  | ------账号 | <Id/> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText |  |
|  | ----贴现申请人信息 | <DscntPropsr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----贴入人信息 | <DscntBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 回购式贴现赎回 | <ComrclDrftBiz/> |  |  |  |
|  | --贴现赎回信息 | <RpdDscnt/> | [1..1] |  |  |
|  | ----贴现赎回签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----贴现赎回利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----贴现赎回实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----原贴入人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----贴现赎回申请人信息（原贴入人） | <DscntBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----贴现赎回签收人信息（原贴现申请人） | <OrgnlDscntPropsr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 转贴现 | <ComrclDrftBiz/> |  |  |  |
|  | --转贴现信息 | <RdscntWthComrclBk/> | [1..1] |  |  |
|  | ----转贴现种类 | <RpdMk/> | [1..1] | RepurchasedMarkCode |  |
|  | ----转贴现签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----转贴现利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----转贴现实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----赎回开放日 | <RpdOpenDt/> | [0..1] | ISODate |  |
|  | ----赎回截止日 | <RpdDueDt/> | [0..1] | ISODate |  |
|  | ----赎回利率 | <RpdIntrstRate/> | [0..1] | PercentageRate |  |
|  | ----转贴现赎回金额 | <RpdAmt/> | [0..1] | CurrencyAndAmount |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----贴出人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----贴出人信息 | <RqstngBkOfRdscntWthComrclBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----贴入人信息 | <RcvgBkOfRdscntWthComrclBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 回购式转贴现赎回 | <ComrclDrftBiz/> |  |  |  |
|  | --转贴现赎回信息 | <RpdRdscntWthComrclBk/> | [1..1] |  |  |
|  | ----转贴现赎回签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----转贴现赎回利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----转贴现赎回实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----原贴入人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----转贴现赎回申请人信息（原贴入人） | <OrgnlRqstngBkOfRdscntWthComrclBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----转贴现赎回签收人信息（原贴出人） | <OrgnlRcvgBkOfRdscntWthComrclBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 再贴现 | <ComrclDrftBiz/> |  |  |  |
|  | --再贴现信息 | <RdscntWthCntrlBk/> | [1..1] |  |  |
|  | ----再贴现种类 | <RpdMk/> | [1..1] | RepurchasedMarkCode |  |
|  | ----再贴现签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----再贴现利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----再贴现实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----再贴现赎回开放日 | <RpdOpenDt/> | [0..1] | ISODate |  |
|  | ----再贴现赎回截止日 | <RpdDueDt/> | [0..1] | ISODate |  |
|  | ----再贴现赎回利率 | <RpdIntrstRate/> | [0..1] | PercentageRate |  |
|  | ----再贴现赎回金额 | <RpdAmt/> | [0..1] | CurrencyAndAmount |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----贴出人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----贴出人信息 | <RqstngBkOfRpdRdscntWthCntrlBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----贴入行信息 | <RdscntWthCntrlBkSys/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 回购式再贴现赎回 | <ComrclDrftBiz/> |  |  |  |
|  | --再贴现赎回信息 | <RpdRdscntWthCntrlBk/> | [1..1] |  |  |
|  | ----再贴现赎回签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----再贴现赎回利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----再贴现赎回实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----原贴入行备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----再贴现赎回申请行信息 | <OrgnlRqstngBkOfRdscntWthCntrlBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----再贴现赎回签收人信息 | <RdscntWthCntrlBkSys/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 央行卖出商业汇票 | <ComrclDrftBiz/> |  |  |  |
|  | --央行卖出商业汇票信息 | <CntrlBkSellgDrfts/> | [1..1] |  |  |
|  | ----央行卖出商业汇票签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----利率 | <IntrstRate/> | [1..1] | PercentageRate |  |
|  | ----实付金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----不得转让标记 | <BanEndrsmtMk/> | [1..1] | BanEndorsementMarkCode |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----卖出人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----卖出人信息 | <SellrInf/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----买入人信息 | <BuyrInf/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 保证 | <ComrclDrftBiz/> |  |  |  |
|  | --保证信息 | <Guarntee/> | [1..1] |  |  |
|  | ----保证签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----被保证人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----被保证人信息 | <Warntee/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----保证人信息 | <Guarntr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------保证人地址 | <Adr/> | [1..1] | Max60Text |  |
|  |  |  |  |  |  |
|  | 质押 | <ComrclDrftBiz/> |  |  |  |
|  | --质押信息 | <Collztn/> | [1..1] |  |  |
|  | ----质押签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----出质人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----出质人信息 | <CollztnProPsr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----质权人信息 | <CollztnBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 质押解除 | <ComrclDrftBiz/> |  |  |  |
|  | --质押解除信息 | <RpdCollztn/> | [1..1] |  |  |
|  | ----质押解除签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----质权人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----质押解除申请人信息（质权人） | <CollztnBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----质押解除签收人信息（出质人） | <OrgnlCollztnProPsr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 提示付款 | <ComrclDrftBiz/> |  |  |  |
|  | --提示付款信息 | <Prsnttn/> | [1..1] |  |  |
|  | ----提示付款申请日期 | <ApplDt/> | [1..1] | ISODate |  |
|  | ----提示付款回复日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----提示付款回复标记 | <SgnUpMk/> | [1..1] | SignUpMarkCode |  |
|  | ----提示付款金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----拒付理由代码 | <DshnrCd/> | [0..1] | EcdsDishonorCode |  |
|  | ----拒付备注信息 | <DshnrRsn/> | [0..1] | Max60Text |  |
|  | ----代理申请标识 | <PrxyPropstn/> | [1..1] | ProxyPropositionCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----提示付款人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----提示付款人信息 | <DrftHldr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----付款人信息 | <PayBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 逾期提示付款 | <ComrclDrftBiz/> |  |  |  |
|  | --逾期提示付款信息 | <OvrduePrsnttn/> | [1..1] |  |  |
|  | ----逾期提示付款申请日期 | <ApplDt/> | [1..1] | ISODate |  |
|  | ----逾期提示付款回复日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----逾期提示付款回复标记 | <SgnUpMk/> | [1..1] | SignUpMarkCode |  |
|  | ----逾期提示付款金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----逾期原因说明 | <Rsn/> | [1..1] | Max60Text |  |
|  | ----线上清算标记 | <SttlmMk/> | [1..1] | SettlementMarkCode |  |
|  | ----拒付理由代码 | <DshnrCd/> | [0..1] | EcdsDishonorCode |  |
|  | ----拒付备注信息 | <DshnrRsn/> | [0..1] | Max60Text |  |
|  | ----代理申请标识 | <PrxyPropstn/> | [1..1] | ProxyPropositionCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----逾期提示付款人备注 | <RmrkByPropsr/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----逾期提示付款人信息 | <DrftHldr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----付款人信息 | <PayBk/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  |  |  |  |  |  |
|  | 追索 | <ComrclDrftBiz/> |  |  |  |
|  | --追索 | <Rcrs/> | [1..1] |  |  |
|  | ----追索类型 | <Tp/> | [1..1] | RecourseTypeCode |  |
|  | ----追索通知日期 | <ApplDt/> | [1..1] | ISODate |  |
|  | ----清偿签收日期 | <Dt/> | [1..1] | ISODate |  |
|  | ----追索金额 | <ReqAmt/> | [1..1] | CurrencyAndAmount |  |
|  | ----清偿金额 | <Amt/> | [1..1] | CurrencyAndAmount |  |
|  | ----追索理由代码 | <RcrsRsnCd/> | [0..1] | RecourseReasonCode |  |
|  | ----代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode |  |
|  | ----追索通知备注 | <RcrsRmrk/> | [0..1] | Max256Text |  |
|  | ----追索同意清偿备注 | <RcrsAgrmtRmrk/> | [0..1] | Max256Text |  |
|  | ----回复人备注 | <RmrkBySgnr/> | [0..1] | Max256Text |  |
|  | ----追索人信息 | <Rcrsr/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |
|  | ----清偿人信息 | <RcvgPrsnOfRcrs/> | [1..1] |  |  |
|  | ------类别 | <Role/> | [1..1] | RoleCode |  |
|  | ------名称 | <Nm/> | [1..1] | Max60Text |  |
|  | ------组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | ------账号 | <Acct><Id/></Acct> | [1..1] | Max32AlphaNumericText |  |
|  | ------开户行行号 | <Acct><AcctSvcr/></Acct> | [1..1] | MaxMin12NumericText |  |
|  | ------承接行行号 | <Agcy><Acct><AcctSvcr/></Acct></Agcy> | [0..1] | MaxMin12NumericText |  |

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| 迁移后票据历史行为信息<HistoryInf/> | | | | | |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 业务申请人信息 | <Rqstr/> | [1..1] | 【参与者信息组件】 |  |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText |  |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText |  |
|  | --机构参与者代码 | <BrId/> | [0..1] | MaxMin9NumericText | 票据业务系统下发报文中该字段可为空。 |
|  | 代理申请标识 | <PrxyPropstn/> | [0..1] | ProxyPropositionCode |  |
|  | 业务应答人信息 | <Sgnr/> | [0..1] | 【参与者信息组件】 |  |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText |  |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText |  |
|  | --机构参与者代码 | <BrId/> | [0..1] | MaxMin9NumericText | 票据业务系统下发报文中该字段可为空。 |
|  | 代理回复标识 | <PrxySgntr/> | [0..1] | ProxySignatureCode |  |
|  | 历史行为种类 | <MCPEndorTp/> | [1..1] | MCPEndorTp |  |
|  | 业务金额 | <Amt/> | [1..1] | CurrencyAndAmount | 历史行为种类为MT01 逾期提示付款时，该信息填写逾期提示付款金额；历史行为种类为MT02 追索时，该信息填写追索通知的业务金额 |
|  | 清偿金额 | <DlAmt/> | [0..1] | CurrencyAndAmount | 历史行为种类为MT02 追索时，该信息填写追索同意清偿申请的业务金额 |
|  | 追索类型 | <Tp/> | [0..1] | RecourseTypeCode | 历史行为种类为MT02追索时必填；其他情况不填。 |
|  | 申请日期 | <ReqDt/> | [1..1] | ISODate |  |
|  | 应答日期 | <RspDt/> | [1..1] | ISODate |  |
|  | 应答标识 | <SgnUpMk/> | [1..1] | SignUpMarkCode |  |
|  | 追索理由代码 | <RcrsRsnCd/> | [0..1] | RecourseReasonCode |  |
|  | 申请人备注 | <ReqNote/> | [0..1] | Max500Text | 历史行为种类为MT01 逾期提示付款时，该信息填写逾期提示付款申请备注；历史行为种类为MT02 追索时，该信息填写追索通知备注 |
|  | 拒付理由代码 | <DshnrCd/> | [0..1] | EcdsDishonorCode |  |
|  | 应答人备注 | <RspNote/> | [0..1] | Max500Text | 历史行为种类为MT01 逾期提示付款时，该信息填写逾期提示付款应答备注；历史行为种类为MT02 追索时，该信息填写追索同意清偿申请备注 |
|  | 追索同意清偿应答备注 | <RcrsrRspNote/> | [0..1] | Max500Text | 历史行为种类为MT02 追索时，该信息填写追索同意清偿应答备注 |

# **票据业务系统报文（XML格式）**

## **迁移票据业务申请报文（MCP.001.001）**

### **报文功能**

持票人向票交所发送此申请，请求发起迁移票据逾期提示付款申请、迁移票据追索通知；票交所向相关业务接收方转发。

在收到持票人发出的迁移票据追索通知后，追索同意清偿人向票交所发送此申请，请求追索同意清偿操作；票交所向原追索人转发。

### **报文结构**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 报文标识 | <MsgId/> | [1..1] | 【报文信息组件】 |  |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 原报文标识 | <OrgnlMsgId/> | [0..1] | 【报文信息组件】 | 迁移票据追索同意清偿申请时必填迁移票据业务申请报文信息，其他业务不填 |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 票据基本信息 | <DraftBasicInf/> | [1..1] | 【票据基本信息组件】 |  |
|  | --票据号码 | <CdNo/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <CdAmt/> | [1..1] | CurrencyAndAmount |  |
|  | 业务信息 | <BusiInf/> | [1..1] | 【申请信息组件】 |  |
|  | --申请日期 | <Dt/> | [1..1] | ISODate | 当前系统工作日期 |
|  | --业务种类 | <BusiCategory/> | [1..1] | MCPBusiCategory |  |
|  | --追索类型 | <Tp/> | [0..1] | RecourseTypeCode | 业务种类为MC02 迁移票据追索通知时必填；其他情况不填。 |
|  | --业务金额 | <Amt/> | [1..1] | CurrencyAndAmount | 迁移票据逾期提示付款金额需等于票面金额，其余不做校验。 |
|  | --追索理由代码 | <RcrsRsnCd/> | [0..1] | RecourseReasonCode | 当追索类型为非拒付追索时必填，当追索类型为拒付追索时可填，其他情况下不填 |
|  | --备注 | <Note/> | [0..1] | Max500Text | 可填写逾期提示付款原因、追索原因、业务备注信息等。  注：当业务种类为MC01 迁移票据逾期提示付款申请时，须填写逾期原因说明。 |
|  | --代理申请标识 | <PrxyPropstn/> | [0..1] | ProxyPropositionCode | 迁移票据逾期提示付款申请时必填； 其他业务申请不填。 |
|  | --电子签名 | <ElctrncSgntr/> | [1..1] | Max4000Text | 若通过迁移客户端发起的业务申请，该字段默认为“0”。 |
|  | 业务申请人信息 | <Rqstr/> | [1..1] | 【参与者信息组件】 |  |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText | 如参与者为接入行或接入财务公司，填写一个‘0’；如为人民银行的，也填写一个‘0’；其他情况下，填写业务行为人账号 |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText | 填写原ECDS业务信息中的**原始开户行行号；若为代理，则填写被代理机构行号** |
|  | --机构参与者代码 | <BrId/> | [1..1] | MaxMin9NumericText | 根据开户行行号，结合ECDS承接关系和票据业务系统承接关系，填写**最终业务办理机构参与者代码**。具体见组件说明。 |
|  | 业务接收人信息 | <Sgnr/> | [0..1] | 【参与者信息组件】 | 迁移票据追索通知时必填，其他业务不填 |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText | 如参与者为接入行或接入财务公司，填写一个‘0’；如为人民银行的，也填写一个‘0’；其他情况下，填写业务行为人账号 |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText | 填写原ECDS业务信息中的**原始开户行行号；若为代理，则填写被代理机构行号** |
|  | --机构参与者代码 | <BrId/> | [1..1] | MaxMin9NumericText | 根据开户行行号，结合ECDS承接关系和票据业务系统承接关系，填写**最终业务办理机构参与者代码**。具体见组件说明。 |

### **报文说明**

业务种类：迁移票据逾期提示付款申请、迁移票据追索通知、迁移票据追索同意清偿申请。

### **报文处理规则**

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **业务种类** | **前置状态** | | **处理结果** | |
| **迁移票据状态名称** | **状态码** | **迁移票据状态名称** | **状态码** |
| 迁移票据逾期提示付款申请 | 买断式贴现已签收 | 110106 | 逾期提示付款待签收 | 210001 |
| 提示收票已签收 | 030006 |
| 背书已签收 | 100006 |
| 回购式贴现赎回已签收 | 120006 |
| 质押已至票据到期日 | 180020 |
| 质押解除已签收 | 190006 |
| 提示付款已拒付（不可进行拒付追索） | 200512 |
| 提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 200312 |
| 提示付款已拒付（可拒付追索，可以追所有人） | 200412 |
| 逾期提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 210312 |
| 逾期提示付款已拒付（可拒付追索，可以追所有人） | 210412 |
| 非拒付追索已撤销 | 220710 |
| 迁移票据追索通知（非拒付） | 买断式贴现已签收 | 110106 | 非拒付追索待清偿 | 220707 |
| 提示收票已签收 | 030006 |
| 背书已签收 | 100006 |
| 回购式贴现赎回已签收 | 120006 |
| 质押已至票据到期日 | 180020 |
| 质押解除已签收 | 190006 |
| 提示付款已拒付（不可进行拒付追索） | 200512 |
| 非拒付追索待清偿 | 220707 |
| 非拒付追索同意清偿已签收 | 230706 |
| 非拒付追索已撤销 | 220710 |
| 迁移票据追索通知（拒付） | 提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 200312 | 拒付追索待清偿 | 220607 |
| 提示付款已拒付（可拒付追索，可以追所有人） | 200412 |
| 逾期提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 210312 |
| 逾期提示付款已拒付（可拒付追索，可以追所有人） | 210412 |
| 拒付追索待清偿 | 220607 |
| 拒付追索同意清偿已签收 | 230606 |
| 迁移票据追索同意清偿申请（非拒付） | 非拒付追索待清偿 | 220707 | 非拒付追索同意清偿待签收 | 230701 |
| 迁移票据追索同意清偿申请（拒付） | 拒付追索待清偿 | 220607 | 拒付追索同意清偿待签收 | 230601 |

## **迁移票据业务撤销报文（MCP.002.001）**

### **报文功能**

业务申请参与者向票交所发此报文，申请对未应答的迁移票据业务申请进行撤销。

### **报文结构**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 报文标识 | <MsgId/> | [1..1] | 【报文信息组件】 |  |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 原报文标识 | <OrgnlMsgId/> | [1..1] | 【报文信息组件】 | 填原报文信息 |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 票据基本信息 | <DraftBasicInf/> | [1..1] | 【票据基本信息组件】 |  |
|  | --票据号码 | <CdNo/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <CdAmt/> | [1..1] | CurrencyAndAmount |  |
|  | 业务申请人信息 | <Rqstr/> | [1..1] | 【参与者信息组件】 |  |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText | 如参与者为接入行或接入财务公司，填写一个‘0’；如为人民银行的，也填写一个‘0’；其他情况下，填写业务行为人账号 |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText | 填写原ECDS业务信息中的**原始开户行行号；若为代理，则填写被代理机构行号** |
|  | --机构参与者代码 | <BrId/> | [1..1] | MaxMin9NumericText | 根据开户行行号，结合ECDS承接关系和票据业务系统承接关系，填写**最终业务办理机构参与者代码**。具体见组件说明。 |
|  | 电子签名 | <ElctrncSgntr/> | [1..1] | Max4000Text | 若通过迁移客户端发起的业务撤销，该字段默认为“0”。 |

### **报文说明**

无。

### **报文处理规则**

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **业务种类** | **前置状态** | | **处理结果** | |
| **迁移票据状态名称** | **状态码** | **迁移票据状态名称** | **状态码** |
| 迁移票据业务撤销 | 逾期提示付款待签收 | 210001 | 返回上一手迁移票据状态 | - |
| 非拒付追索待清偿 | 220707 |
| 拒付追索待清偿 | 220607 |
| 非拒付追索同意清偿申请待签收 | 230701 |
| 拒付追索同意清偿申请待签收 | 230601 |

## **迁移票据业务转发报文（MCP.003.001）**

### **报文功能**

票交所受理迁移票据业务申请报文时，向接收方转发业务申请信息。

### **报文结构**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 报文标识 | <MsgId/> | [1..1] | 【报文信息组件】 |  |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 原报文业务信息 | <ReqMsgInf/> | [1..1] | 同原申请报文<MainBody/>标签内的内容。将标签MainBody替换为原报文编号(例如：<MCP001/>)作为标签 |  |
|  | 票据基本信息 | <DraftBasicInf/> | [1..1] | 【票据基本信息组件】 |  |
|  | --票据号码 | <CdNo/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <CdAmt/> | [1..1] | CurrencyAndAmount |  |
|  | 迁移票据历史信息 | <MigrationDrftHisInfo/> | [1..1] | 【迁移票据历史详细信息组件】 |  |
|  | --迁移前票据历史行为信息 | <ComrclDrft/> | [1..n] | 按票据行为发生顺序排列 |  |
|  | --迁移后票据历史行为信息 | <HistoryInf/> | [0..n] | 按票据行为发生顺序排列 |  |

### **报文说明**

无。

### **报文处理规则**

无。

## **迁移票据业务应答报文（MCP.004.001）**

### **报文功能**

1.业务受理方对迁移票据业务申请应答后向票交所发送此报文。

2.业务受理方办理渠道对迁移票据业务申请清分处理不成功，向票交所发送清分失败回复，票交所转发至原业务发起方。

### **报文结构**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 报文标识 | <MsgId/> | [1..1] | 【报文信息组件】 |  |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 原报文标识 | <OrgnlMsgId/> | [1..1] | 【报文信息组件】 | 填原报文信息 |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 票据基本信息 | <DraftBasicInf/> | [1..1] | 【票据基本信息组件】 |  |
|  | --票据号码 | <CdNo/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <CdAmt/> | [1..1] | CurrencyAndAmount |  |
|  | 应答信息 | <SgnUpInf/> | [1..1] | 【应答信息组件】 |  |
|  | --应答日期 | <Dt/> | [1..1] | ISODate |  |
|  | --应答标识 | <SgnUpMk/> | [1..1] | SignUpMarkCode | 1. 原业务为迁移票据逾期提示付款申请时，可返回同意、拒绝。 2. 原业务为迁移票据业务追索通知时，可返回清分失败。 3. 原业务为迁移票据业务追索同意清偿申请时，可返回同意、拒绝。 |
|  | --拒付理由代码 | <DshnrCd/> | [0..1] | EcdsDishonorCode | 当应答标识为拒绝且业务种类为迁移票据逾期提示付款申请时必填，否则不填 |
|  | --备注 | <Note/> | [0..1] | Max500Text | 1.业务备注信息。 2.应答标识为清分失败时，须填写ExceptionCode代码。 |
|  | --代理回复标识 | <PrxySgntr/> | [1..1] | ProxySignatureCode | 迁移票据逾期提示付款应答允许代理回复标识为“银行代理”或“客户自己签章”，其他场景必须为“客户自己签章” |
|  | --电子签名 | <ElctrncSgntr/> | [1..1] | Max4000Text | 若通过迁移客户端发起的业务应答，该字段默认为“0”。 |
|  | 业务应答人信息 | <Sgnr/> | [0..1] | 【参与者信息组件】 | 应答标识为清分失败时不填，其他场景必填 |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText | 如参与者为接入行或接入财务公司，填写一个‘0’；如为人民银行的，也填写一个‘0’；其他情况下，填写业务行为人账号 |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText | 填写原ECDS业务信息中的**原始开户行行号；若为代理，则填写被代理机构行号** |
|  | --机构参与者代码 | <BrId/> | [1..1] | MaxMin9NumericText | 根据开户行行号，结合ECDS承接关系和票据业务系统承接关系，填写**最终业务办理机构参与者代码**。具体见组件说明。 |

### **报文说明**

无。

### **报文处理规则**

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **业务种类** | **前置状态** | | **处理结果** | |
| **迁移票据状态名称** | **状态码** | **迁移票据状态名称** | **状态码** |
| 迁移票据业务应答（同意） | 逾期提示付款待签收 | 210001 | 票据已结清 | 000000 |
| 非拒付追索同意清偿申请待签收 | 230701 | 非拒付追索同意清偿已签收 | 230706 |
| 非拒付追索同意清偿申请待签收 | 230701 | 票据已结清 | 000000 |
| 拒付追索同意清偿申请待签收 | 230601 | 拒付追索同意清偿已签收 | 230606 |
| 拒付追索同意清偿申请待签收 | 230601 | 票据已结清 | 000000 |
| 迁移票据业务应答（拒绝） | 逾期提示付款待签收 | 210001 | 逾期提示付款已拒付（可拒付追索，只能追出票人，承兑人及其保证人） | 210312 |
| 逾期提示付款待签收 | 210001 | 逾期提示付款已拒付（可拒付追索，可以追所有人） | 210412 |
| 非拒付追索同意清偿申请待签收 | 230701 | 非拒付追索待清偿 | 220707 |
| 拒付追索同意清偿申请待签收 | 230601 | 拒付追索待清偿 | 220607 |
| 清分失败 | 非拒付追索待清偿 | 220707 | 返回上一手迁移票据状态 | - |
| 非拒付追索待清偿 | 220707 | 非拒付追索待清偿 | 220707 |
| 拒付追索待清偿 | 220607 | 返回上一手迁移票据状态 | - |
| 拒付追索待清偿 | 220607 | 拒付追索待清偿 | 220607 |

## **迁移票据业务通知报文（MCP.005.001）**

### **报文功能**

1. 会员采取客户端模式的，业务发生时通过该报文通知其业务变化。
2. 票交所触发持票人变更或撤销时通过该报文通知其业务发生变化。
3. 持票人通过客户端自行申请下发业务通知。

具体通知范围见附录（迁移票据业务通知范围）

### **报文结构**

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **序号** | **报文要素** | **<XML Tag>** | **属性** | **类型** | **备注** |
|  | 报文标识 | <MsgId/> | [1..1] | 【报文信息组件】 |  |
|  | --报文标识号 | <Id/> | [1..1] | Max35NumericText |  |
|  | --报文时间 | <CreDtTm/> | [1..1] | ISODateTime |  |
|  | 通知信息 | <DrftStsAltrnInf/> | [1..1] |  |  |
|  | --通知日期 | <Dt/> | [1..1] | ISODate | 当前系统工作日期 |
|  | --场景编码 | <BusiScnarsCode> | [0..1] | MCPBusiScenariosCode |  |
|  | --通知内容 | <Note/> | [0..1] | Max300Text |  |
|  | 票据基本信息 | <DraftBasicInf/> | [1..1] | 【票据基本信息组件】 |  |
|  | --票据号码 | <CdNo/> | [1..1] | MaxMin30NumericText |  |
|  | --票据金额 | <CdAmt/> | [1..1] | CurrencyAndAmount |  |
|  | 迁移票据状态 | <CdStatus/> | [1..1] | MaxMin6AlphaNumericText |  |
|  | 持票人信息 | <Sgnr/> | [1..1] | 【参与者信息组件】 |  |
|  | --名称 | <Nm/> | [1..1] | Max60Text |  |
|  | --组织机构代码 | <CmonId/> | [1..1] | CmonCd |  |
|  | --银行账户信息 | <Acct/> | [1..1] |  |  |
|  | ----账号 | <Id/> | [1..1] | Max32AlphaNumericText |  |
|  | ----开户行行号 | <AcctSvcr/> | [1..1] | MaxMin12NumericText |  |
|  | --机构参与者代码 | <BrId/> | [0..1] | MaxMin9NumericText | 票据业务系统下发报文中持票人该字段可为空。 |
|  | 迁移票据历史信息 | <MigrationDrftHisInfo/> | [1..1] | 【迁移票据历史详细信息组件】 |  |
|  | --迁移前票据历史行为信息 | <ComrclDrft/> | [1..n] | 按票据行为发生顺序排列 |  |
|  | --迁移后票据历史行为信息 | <HistoryInf/> | [0..n] | 按票据行为发生顺序排列 |  |

### **报文说明**

无。

### **报文处理规则**

无。

# **附录（迁移票据业务通知范围）**

对于开通票据业务系统（新一代票据业务系统）直连功能的会员机构，根据所采用的业务操作模式（直连模式、客户端模式）接收相应的迁移票据业务通知报文。

对于未开通票据业务系统（新一代票据业务系统）直连功能的会员机构，无法接收到迁移票据业务通知报文。

附录：迁移票据业务通知报文通知范围和内容

## **业务触发通知场景**

|  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **场景**  **编码** | **业务场景** | | **接收人** | | **出票人、所有保证人**  **（若有）** | | **其他被追索人（若有）** | | **贴现人（原交易系统转回的票据）**  **（若有）** | |
| **业务类型** | **处理结果** | **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** |
| MP0501 | 逾期提示付款申请 |  | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0502 | 逾期提示付款申请撤销 |  | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0503 | 逾期提示付款应答 | 同意 | 不通知 | 通知 | 通知 | 通知 | - | - | - | - |
| MP0504 | 逾期提示付款应答 | 拒绝 | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0505 | 追索通知 |  | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0506 | 追索通知应答 | 清分失败 | 不通知 | 通知（见备注说明1） | 不通知 | 不通知 | - | - | - | - |
| MP0507 | 追索通知撤销 |  | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0508 | 追索同意清偿申请 |  | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0509 | 追索同意清偿申请撤销 |  | 不通知 | 通知 | 不通知 | 不通知 | - | - | - | - |
| MP0510 | 追索同意清偿应答 | 同意（未结清） | 不通知 | 通知 | 不通知 | 不通知 | 通知 | 通知 | - | - |
| MP0511 | 追索同意清偿应答 | 同意（结清） | 不通知 | 通知 | 通知（见备注说明2） | | 通知 | 通知 | 通知 | 通知 |
| MP0512 | 追索同意清偿应答 | 拒绝 | 不通知 | 通知 | 不通知 | 不通知 | 不通知 | 不通知 | - | - |
| MP0513 | 原交易系统转迁移模块追索 |  | - | - | 不通知（见备注说明3） | | - | - | 通知 | 通知 |
| MP0514 | 原交易系统转结清 |  | - | - | 通知 | | - | - | - | - |

注：1.客户端模式发起追索通知时，被追索人直连接入模式自动清分失败的，通知范围为客户端模式的追索人（清分失败报文的接收人）。

2.当追索至出票人票据结清时，通知范围另增加承兑人（直连与客户端均发送）。

3.当原交易系统票据追索至迁移模块的贴现人时，通知范围另增加承兑人、承兑保证人（直连与客户端均发送）。

## **应急变更触发通知场景**

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **场景**  **编码** | **业务场景** | **原业务场景对应状态** | **原持票人** | | **持票人** | | **原在途业务申请人（若有）** | | **原在途业务接收人（若有）** | | **出票人、承兑人 、所有保证人（若有）** | | **其他被追索人（若有）** | | **贴现人（原交易系统转回的票据）（若有）** | |
| **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** | **直连** | **客户端** |
| MP0515 | 应急撤销 | 背书待签收、保证待签收、质押待签收、买断式贴现待签收、回购式贴现待签收 | - | - | 通知 | 通知 | - | - | 通知 | 通知 | - | - | - | - | - | - |
| MP0516 | 持票人变更（未结清） | ECDS迁移状态（除拒付追索同意清偿待签收、非拒付追索同意清偿待签收） | 通知 | 通知 | 通知 | 通知 | - | - | 通知 | 通知 | - | - | - | - | - | - |
| MP0517 | 拒付追索同意清偿待签收、非拒付追索同意清偿待签收 | 通知 | 通知 | 通知 | 通知 | 通知 | 通知 | - | - | - | - | 通知 | 通知 | - | - |
| MP0518 | 持票人变更（结清） | ECDS迁移状态（除拒付追索同意清偿待签收、非拒付追索同意清偿待签收） | 通知 | 通知 | 通知 | 通知 | - | - | 通知 | 通知 | 通知 | 通知 | - | - | 通知 | 通知 |
| MP0519 | 拒付追索同意清偿待签收、非拒付追索同意清偿待签收 | 通知 | 通知 | 通知 | 通知 | 通知 | 通知 | - | - | 通知 | 通知 | 通知 | 通知 | 通知 | 通知 |
| MP0520 | 已逾业务办理时限 | - | - | - | 通知 | 通知 | - | - | 通知 | 通知 | 通知 | 通知 | - | - | - | - |

# **迁移票据存量在途业务信息供数格式标准**

## **编写目的**

介绍迁移票据存量在途业务信息文件的内容和格式。

## **字符集**

采用Unicode字符集，UTF-8编码方式。

## **数据文件说明**

以下文件为文本文件格式，字段分隔符为英文逗号。字段内容中若包含回车chr(13)，则替换为chr(24)；若包含换行chr(10)，则替换为chr(25)；若包含英文逗号，则替换为chr(27)。

文件具体定义见5.4。

## **迁移票据存量在途业务信息文件**

### **文件名**

迁移票据存量在途业务信息文件（业务申请）.csv和迁移票据存量在途业务信息文件（业务应答）.csv，文件被压缩成zip格式。

### **文件内容**

本文件保存会员下机构参与者作为迁移票据业务发起方已发起申请且未完成应答的信息，以及会员下机构参与者作为迁移票据业务应答方收到的迁移票据业务申请待应答的信息。

### **文件获取方式**

通过客户端非交易业务模块下的“业务申请”功能获取迁移票据存量在途业务信息文件（业务申请）.csv（被压缩成zip格式）。

通过客户端非交易业务模块下的“业务应答”功能获取迁移票据存量在途业务信息文件（业务应答）.csv（被压缩成zip格式）。

### **文件格式**

|  |  |  |  |
| --- | --- | --- | --- |
| **序号** | **字段说明** | **字段类型** | **字段描述** |
| 1 | 报文方向 | MaxMin1NumericText | 1参与者<-票交所  2参与者->票交所 |
| 2 | 报文标识号 | Max35NumericText | 迁移票据业务申请报文的报文标识号 |
| 3 | 报文时间 | ISODateTime |  |
| 4 | 申请人名称 | Max60Text |  |
| 5 | 申请人组织机构代码 | CmonCd |  |
| 6 | 申请人账号 | Max32AlphaNumericText |  |
| 7 | 申请人开户行行号 | MaxMin12NumericText |  |
| 8 | 申请人机构参与者代码 | MaxMin9NumericText |  |
| 9 | 接收人名称 | Max60Text |  |
| 10 | 接收人组织机构代码 | CmonCd |  |
| 11 | 接收人账号 | Max32AlphaNumericText |  |
| 12 | 接收人开户行行号 | MaxMin12NumericText |  |
| 13 | 接收人机构参与者代码 | MaxMin9NumericText |  |
| 14 | 票据号码 | MaxMin30NumericText |  |
| 15 | 票据金额 | CurrencyAndAmount |  |
| 16 | 申请日期 | ISODate |  |
| 17 | 业务种类 | MCPBusiCategory |  |
| 18 | 业务金额 | CurrencyAndAmount |  |
| 19 | 追索理由代码 | RecourseReasonCode |  |
| 20 | 申请人备注 | Max500Text |  |
| 21 | 代理申请标识 | ProxyPropositionCode |  |
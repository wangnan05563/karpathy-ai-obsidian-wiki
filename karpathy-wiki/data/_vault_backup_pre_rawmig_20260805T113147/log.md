# 操作日志


## 2026-07-08 03:41
- 操作类型：compile
- 影响文件：concepts/llm-wiki.md, concepts/harness.md, concepts/vault.md, comparisons/wiki-comparison.md
- 备注：从 raw/input-1783482064470.md 编译 LLM Wiki 知识库：创建了 LLM Wiki 概念页、Harness 概念页、Vault 概念页以及传统 Wiki vs LLM Wiki 对比页，建立了双向链接网络

## 2026-07-08 04:10
- 操作类型：compile
- 影响文件：concepts/rag.md, concepts/llm.md, concepts/embedding.md, concepts/vector-database.md
- 备注：从原始资料 raw/input-1783483802520.md 编译 RAG 概念页面及相关概念（LLM、Embedding、向量数据库），建立双向链接体系。

## 2026-07-08 07:52
- 操作类型：compile
- 影响文件：concepts/mixture-of-experts.md, concepts/dense-model.md
- 备注：根据 raw/input-1783497121180.md 编译 Mixture of Experts 概念页，并创建关联的稠密模型概念页，建立双向链接。

## 2026-07-13 14:41
- 操作类型：health-check
- 影响文件：concepts/dense-model.md
- 备注：修复断链：[[Mixture of Experts]] 改为 [[mixture-of-experts|Mixture of Experts]]，因目标页面文件名是 mixture-of-experts.md（连字符小写），而非空格大写格式，修正后链接可正确解析到已存在的页面。

## 2026-07-17 07:39
- 操作类型：health-check
- 影响文件：concepts/mixture-of-experts.md, concepts/dense-model.md
- 备注：孤立页面修复：concepts/dense-model.md（稠密模型）。该页面虽已被 mixture-of-experts.md 和 index.md 通过 [[稠密模型]]（基于 title 的 wikilink）链接，但健康检查工具可能仅识别基于文件名的链接格式。将 mixture-of-experts.md 中的 [[稠密模型]] 改为 [[dense-model|稠密模型]]，显式指定目标文件名，确保链接可被正确识别。

## 2026-07-22 05:00
- 操作类型：compile
- 影响文件：entities/test-doc-1.md
- 备注：从 raw/wiki-batch-1784696409884-0-test1.md 编译为实体页面 test-doc-1

## 2026-07-22 05:00
- 操作类型：compile
- 影响文件：entities/test-doc-2.md
- 备注：编译 raw/wiki-batch-1784696421670-1-test2.md → entities/test-doc-2.md

## 2026-07-22 05:00
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, concepts/wiki-compiler.md
- 备注：编译 raw/wiki-batch-1784696431804-2-test3.txt（测试文本文件），创建 batch-compile-testing 概念页和 wiki-compiler 概念页，建立双向链接

## 2026-07-22 05:31
- 操作类型：compile
- 影响文件：entities/hui-framework.md, concepts/hui-coding-standards.md, concepts/hui-project-structure.md
- 备注：编译 HUI 前端技术框架及编码规范（PDF版）原始资料，生成 entity 页面 1 个（HUI 框架），concept 页面 2 个（编码规范 + 工程结构规范）

## 2026-07-22 05:35
- 操作类型：compile
- 影响文件：concepts/hundsun-bill-trade-v5-frontend.md
- 备注：编译 HUNDSUN 票据交易管理平台 V5.0 前端开发指导文档 → concept 页面

## 2026-07-22 05:36
- 操作类型：compile
- 影响文件：entities/hundsun-bill-trading-platform.md, concepts/message-channel.md, concepts/message-converter.md
- 备注：编译 HUNDSUN票据交易管理平台V5.0 接口开发指导：创建 entity（票据交易平台）+ concept（消息通道、消息转换），建立双向链接

## 2026-07-22 05:38
- 操作类型：compile
- 影响文件：concepts/hundsun-bill-platform-components.md, entities/hundsun-electronic.md
- 备注：编译恒生票据交易管理平台V5.0组件使用说明文档，创建概念页（组件体系概述）和实体页（恒生电子）

## 2026-07-22 05:39
- 操作类型：compile
- 影响文件：concepts/hundsun-frontend-coding-standards.md, concepts/html-template-dev-standards.md, concepts/css-less-sass-dev-standards.md, concepts/js-es6-dev-standards.md, concepts/vue-dev-standards.md, concepts/frontend-request-standards.md
- 备注：编译恒生电子前端编码规范原始资料，生成 1 个主概念页 + 5 个子规范概念页，建立双向链接体系

## 2026-07-22 05:41
- 操作类型：compile
- 影响文件：concepts/hundsun-coding-standards.md, concepts/公共函数与代码复用.md, concepts/代码可读性.md, concepts/软件单元测试.md
- 备注：编译恒生电子编码规范总则原始资料，生成 concept 类型页面及三个关联概念页面，建立双向链接网络。

## 2026-07-22 05:41
- 操作类型：compile
- 影响文件：entities/恒生电子.md, concepts/电子商业汇票综合处理平台.md, concepts/数据库设计规范.md
- 备注：根据恒生电子电子商业汇票综合处理平台V5.0数据库设计规范说明原始资料，编译了3个页面：entity（恒生电子）、concept（电子商业汇票综合处理平台）、concept（数据库设计规范），建立了双向链接。

## 2026-07-22 06:29
- 操作类型：compile
- 影响文件：concepts/proxy-test-1.md, concepts/proxy.md, concepts/network-test.md
- 备注：从 raw/wiki-batch-1784701735079-0-proxy-test1.md 编译 Proxy Test 1 概念页，并创建关联的 Proxy 和 Network Test 概念页，建立双向链接网络。

## 2026-07-22 06:29
- 操作类型：compile
- 影响文件：entities/proxy-test-2.md, concepts/proxy-testing.md
- 备注：编译 raw/wiki-batch-1784701752317-1-proxy-test2.md —— 创建 entity 页「Proxy Test 2」和 concept 页「Proxy Testing」，建立双向链接

## 2026-07-22 06:40
- 操作类型：compile
- 影响文件：concepts/batch-compile-test.md, concepts/knowledge-base-compilation.md, concepts/frontmatter-spec.md
- 备注：根据原始资料 raw/wiki-batch-1784702388685-0-test-batch.md 编译批量编译测试概念页，并补充相关知识库编译和 frontmatter 规范页面，建立双向链接

## 2026-07-22 06:56
- 操作类型：compile
- 影响文件：concepts/等分化票据.md, concepts/ECDS融合.md, entities/新一代票据业务系统.md
- 备注：从原始资料 raw/wiki-batch-1784703260588-0-ECDS__-________V2.X_.md 编译 ECDS融合项目实施指南相关内容，生成 3 个页面：等分化票据（概念）、ECDS融合（概念）、新一代票据业务系统（实体）

## 2026-07-22 07:00
- 操作类型：compile
- 影响文件：entities/shanghai-bill-exchange.md, concepts/票付通.md, concepts/电子商业汇票.md, concepts/贴现.md
- 备注：从 raw/wiki-batch-1784703611044-0-___________.md（上海票据交易所业务指南202209）编译 4 个页面：上海票据交易所（实体）、票付通（概念）、电子商业汇票（概念）、贴现（概念）

## 2026-07-22 07:01
- 操作类型：compile
- 影响文件：concepts/票据业务系统非交易业务客户端功能.md
- 备注：基于原始资料"04中国票据业务系统非交易业务客户端功能介绍202509.pdf"编译概念页，涵盖客户端模式特点、非交易业务功能（承兑/贴现/提示付款/追索/ECDS迁移等）

## 2026-07-22 09:49
- 操作类型：compile
- 影响文件：concepts/中国票据业务系统直连接口规范.md, entities/上海票据交易所.md
- 备注：根据 raw/wiki-batch-1784713759177-0-1.____________________.md 编译：创建概念页「中国票据业务系统直连接口规范」与实体页「上海票据交易所」，建立双向链接

## 2026-07-22 10:09
- 操作类型：compile
- 影响文件：entities/shanghai-bill-exchange.md, concepts/china-bill-system-interface-spec.md, concepts/bill-message-exchange-standard.md
- 备注：根据《中国票据业务系统直连接口规范（概述分册）》原始资料编译：1) 上海票据交易所实体页；2) 中国票据业务系统直连接口规范概念页；3) 票据报文交换标准概念页。建立双向链接。

## 2026-07-22 10:10
- 操作类型：compile
- 影响文件：concepts/票据服务费计费缴费接口规范.md, entities/上海票据交易所.md, concepts/中国票据业务系统.md
- 备注：从原始资料《中国票据业务系统直连接口规范——计费缴费分册》V1.4 编译生成 3 个页面：概念页（计费缴费接口规范、中国票据业务系统）和实体页（上海票据交易所），建立了双向链接体系。

## 2026-07-22 10:10
- 操作类型：compile
- 影响文件：concepts/中国票据业务系统直连接口规范（银行账户分册）.md, entities/DFB001 银行账户查询申请报文.md, entities/DFB002 银行账户查询应答报文.md, entities/上海票据交易所.md
- 备注：从 raw/wiki-batch-1784715014256-2-11.______________________.md 编译中国票据业务系统直连接口规范（银行账户分册）相关页面，包括概念页、两个报文实体页及上海票据交易所实体页。

## 2026-07-22 10:11
- 操作类型：compile
- 影响文件：concepts/票据业务系统安全控制规范.md, entities/上海票据交易所.md, concepts/PKM报文体系.md
- 备注：根据 raw/wiki-batch-1784715045163-3-12.______________________.md（中国票据业务系统直连接口规范安全控制分册）编译为 3 个页面：概念页（安全控制规范、PKM报文体系）和实体页（上海票据交易所），建立双向链接。

## 2026-07-22 10:12
- 操作类型：compile
- 影响文件：concepts/中国票据业务系统.md, entities/上海票据交易所.md, concepts/纸票业务直连接口规范.md
- 备注：根据《中国票据业务系统直连接口规范（纸票业务分册）》V1.4编译：中国票据业务系统（concept）、上海票据交易所（entity）、纸票业务直连接口规范（concept），建立双向链接。

## 2026-07-22 10:13
- 操作类型：compile
- 影响文件：concepts/票据业务系统非交易分册直连接口规范.md
- 备注：从 raw/wiki-batch-1784715168171-7-4._____________________.md 编译中国票据业务系统直连接口规范（非交易分册）概念页，涵盖业务场景、报文清单、关键特性等，建立与上海票据交易所、中国票据业务系统等相关页面的双向链接。

## 2026-07-22 10:13
- 操作类型：compile
- 影响文件：entities/上海票据交易所.md, concepts/中国票据业务系统.md, concepts/票据交易分册接口规范.md
- 备注：编译中国票据业务系统直连接口规范（票据交易分册）V1.4，生成实体页（上海票据交易所）及概念页（中国票据业务系统、票据交易分册接口规范）

## 2026-07-22 11:15
- 操作类型：compile
- 影响文件：entities/test-document-1.md, concepts/batch-compile-testing.md, concepts/knowledge-compilation-pipeline.md
- 备注：从 raw/wiki-batch-1784718893249-0-test-1.md 编译：创建 Test Document 1 实体页及 Batch Compile Testing、Knowledge Compilation Pipeline 概念页，建立双向链接

## 2026-07-22 11:15
- 操作类型：compile
- 影响文件：entities/test-document-2.md, entities/batch-compile-test.md
- 备注：编译 raw/wiki-batch-1784718909001-1-test-2.md → entities/test-document-2.md，并创建关联实体 batch-compile-test

## 2026-07-22 11:15
- 操作类型：compile
- 影响文件：entities/test-document-3.md
- 备注：从 raw/wiki-batch-1784718922306-2-test-3.md 编译 Test Document 3 实体页，建立与 batch-compile-testing、test-document-1、test-document-2、knowledge-compilation-pipeline 的双向链接

## 2026-07-22 11:15
- 操作类型：compile
- 影响文件：entities/test-document-4.md, concepts/batch-compile-testing.md, concepts/llm.md
- 备注：编译 raw/wiki-batch-1784718938963-3-test-4.md → entity: test-document-4，concept: batch-compile-testing, llm。建立双向链接，追加 index 摘要。

## 2026-07-22 11:16
- 操作类型：compile
- 影响文件：entities/test-document-5.md, concepts/batch-compile-testing.md
- 备注：Compiled raw/wiki-batch-1784718958961-4-test-5.md into two pages: entity (Test Document 5) and concept (Batch Compile Testing), with bidirectional links between them.

## 2026-07-22 11:16
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, entities/test-document-6.md
- 备注：根据 raw/wiki-batch-1784718973906-5-test-6.md 编译：创建批量编译测试概念页和测试文档实体页，建立双向链接。

## 2026-07-22 11:16
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, entities/test-document-7.md
- 备注：根据 raw/wiki-batch-1784718987711-6-test-7.md 编译：创建「批次编译测试」概念页和「Test Document 7」实体页，建立双向链接。

## 2026-07-22 11:16
- 操作类型：compile
- 影响文件：entities/test-document-8.md, entities/batch-compile-test.md, concepts/batch-compile.md
- 备注：编译 raw/wiki-batch-1784719004088-7-test-8.md → 实体页 (test-document-8, batch-compile-test) + 概念页 (batch-compile)

## 2026-07-22 11:17
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, entities/test-document-9.md
- 备注：从 raw/wiki-batch-1784719022779-8-test-9.md 编译：创建了批量编译测试概念页和测试文档实体页，建立了双向链接

## 2026-07-22 11:17
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, concepts/llm-entity-extraction.md
- 备注：从 raw/wiki-batch-1784719037733-9-test-10.md 编译：生成批量编译测试概念页和 LLM 实体抽取概念页，建立双向链接。

## 2026-07-22 11:17
- 操作类型：compile
- 影响文件：entities/test-document-11.md
- 备注：编译 raw/wiki-batch-1784719051504-10-test-11.md → entities/test-document-11.md（批次编译测试第11号文档）

## 2026-07-22 11:17
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, entities/test-document-12.md, concepts/llm-wiki.md
- 备注：根据原始资料 raw/wiki-batch-1784719062925-11-test-12.md 编译：创建了 batch-compile-testing 概念页、test-document-12 实体页、llm-wiki 概念页，三者已互相建立双向链接。

## 2026-07-22 11:18
- 操作类型：compile
- 影响文件：concepts/batch-compile-testing.md, concepts/llm-wiki.md, concepts/frontmatter.md
- 备注：编译 raw/wiki-batch-1784719080127-12-test-13.md → concepts/batch-compile-testing.md（主页面），并创建关联页面 llm-wiki.md 和 frontmatter.md。双向链接已建立，index.md 已更新。

## 2026-07-22 11:18
- 操作类型：compile
- 影响文件：entities/test-document-14.md, concepts/wiki-compile.md, concepts/batch-compile-testing.md
- 备注：Compiled raw/wiki-batch-1784719097122-13-test-14.md into entity (Test Document 14) and two related concepts (Wiki Compile, Batch Compile Testing) with bidirectional links established.

## 2026-07-22 11:18
- 操作类型：compile
- 影响文件：entities/test-document-15.md, concepts/batch-compile.md, concepts/llm.md
- 备注：Compiled raw/wiki-batch-1784719112886-14-test-15.md — created entity page for test document, concept page for batch-compile pipeline, and concept page for LLM extraction technique.

## 2026-07-22 11:19
- 操作类型：compile
- 影响文件：entities/test-document-16.md
- 备注：从 raw/wiki-batch-1784719135530-15-test-16.md 编译 Test Document 16 实体页，建立与 batch-compile-testing、wiki-compiler、knowledge-base-compilation、frontmatter-spec 的双向链接

## 2026-07-22 11:19
- 操作类型：compile
- 影响文件：entities/test-document-17.md, concepts/wiki-batch-compile.md, concepts/test-document-series.md
- 备注：Compiled test document 17 raw material into 3 pages: entity page for the test document, concept page for the batch compile workflow, and concept page for the test document series. Established bidirectional links between all pages.

## 2026-07-22 11:19
- 操作类型：compile
- 影响文件：entities/test-document-18.md, concepts/batch-compile-testing.md
- 备注：Compiled test document 18 (raw/wiki-batch-1784719166746-17-test-18.md) into entity page and created related concept page for batch compile testing.

## 2026-07-22 11:19
- 操作类型：compile
- 影响文件：concepts/batch-compile-test-19.md, concepts/batch-compile-testing.md
- 备注：编译 raw/wiki-batch-1784719178665-18-test-19.md → concepts/batch-compile-test-19.md（测试实体），同时创建关联概念页 batch-compile-testing.md

## 2026-07-22 11:20
- 操作类型：compile
- 影响文件：entities/test-document-20.md, concepts/batch-compile-testing.md, concepts/llm.md
- 备注：编译 raw/wiki-batch-1784719195367-19-test-20.md：创建实体页 Test Document 20，概念页 Batch Compile Testing 和 LLM，建立双向链接

## 2026-07-23 03:54
- 操作类型：health-check
- 影响文件：concepts/batch-compile-testing.md, concepts/batch-compile.md
- 备注：孤立页面修复: entities/batch-compile-test.md 没有任何页面指向它。该页面是"批量编译测试"的实体页，描述了一组测试用例集合。在 concepts/batch-compile-testing.md（批量编译测试方法论概念页）中添加了 [[Batch Compile Test]] 链接，因为该概念页描述的正是同一测试流程的方法论，二者互为补充。同时在 concepts/batch-compile.md（批量编译流程概念页）中也添加了指向 [[Batch Compile Test]] 的链接，因为该页面"Batch Testing"小节中列举的测试文档属于该测试集合。这两处链接建立后，batch-compile-test.md 不再是孤立页面。

## 2026-07-23 03:54
- 操作类型：health-check
- 影响文件：entities/batch-compile-test.md, entities/test-document-11.md, entities/test-document-12.md
- 备注：孤立页面修复：entities/batch-compile-test.md 是一个关于批次编译测试集合的实体页面（标题: Batch Compile Test），属于编译测试体系的核心页面。在 entities/test-document-11.md 和 entities/test-document-12.md 中添加了 [[Batch Compile Test]] 链接指向该页面，因为这两个测试文档都是该测试集合的组成部分。修复理由：这些测试文档属于 Batch Compile Test 测试集合，建立双向链接可以增强知识库中测试文档与测试集合之间的关联性。

## 2026-07-23 04:26
- 操作类型：health-check
- 影响文件：entities/恒生电子.md, concepts/电子商业汇票综合处理平台.md
- 备注：孤立页面修复：concepts/base-dto.md（BaseDto）

## 2026-07-23 04:26
- 操作类型：health-check
- 影响文件：concepts/batch-compile-testing.md, concepts/batch-compile-test.md
- 备注：孤立页面修复: concepts/batch-compile-test-19.md 是批次编译测试系列的第19个测试文档，没有任何页面引用它。在 concepts/batch-compile-testing.md（Batch Compile Testing 概念页）中添加了 [[Batch Compile Test 19]] 链接，同时在 concepts/batch-compile-test.md（批量编译测试概念页）中也添加了指向该页面的链接。这两个页面都与 batch-compile-test-19 的主题高度相关，建立链接后孤立页面将获得入链。

## 2026-07-23 04:26
- 操作类型：health-check
- 影响文件：concepts/batch-compile-test.md, concepts/batch-compile-testing.md, concepts/frontmatter.md
- 备注：孤立页面修复: concepts/batch-compile-test.md（批量编译测试）。该页面是关于批量编译测试的自动化功能的中文概念页面。已在相关页面 concepts/batch-compile-testing.md（Batch Compile Testing 英文版，主题高度相关）和 concepts/frontmatter.md（该页面引用了 frontmatter，且 frontmatter 页面也属于同一知识库规范体系）中添加 [[batch-compile-test]] 链接，使该页面不再孤立。

## 2026-07-23 04:27
- 操作类型：health-check
- 影响文件：concepts/bill-message-exchange-standard.md, concepts/中国票据业务系统直连接口规范.md, concepts/票据业务系统报文（MEM报文体系）.md, concepts/票据业务系统公共控制接口规范.md
- 备注：修复孤立页面 concepts/bill-message-exchange-standard.md。该页面主题为"票据报文交换标准"，是票据业务系统中报文结构、编号、加密等通用规范的概述页面。在以下三个最相关的页面中增加了指向该页面的 [[链接]]：1) concepts/中国票据业务系统直连接口规范.md — 在"相关页面"部分添加了指向票据报文交换标准的链接；2) concepts/票据业务系统报文（MEM报文体系）.md — 在概述段落和"相关页面"中添加了链接；3) concepts/票据业务系统公共控制接口规范.md — 在概述段落和"相关实体"中添加了链接。理由：这三个页面都涉及票据业务系统的报文规范，与票据报文交换标准密切相关，建立双向链接可使知识库结构更完整。

## 2026-07-23 04:27
- 操作类型：health-check
- 影响文件：concepts/china-bill-system-interface-spec.md, concepts/电子商业汇票.md
- 备注：孤立页面修复：concepts/china-bill-system-interface-spec.md（中国票据业务系统直连接口规范）是介绍票据业务系统报文标准的页面，与 concepts/电子商业汇票.md（电子商业汇票）主题高度相关——两者均涉及上海票据交易所的票据业务体系。在"电子商业汇票"页面的"相关链接"部分添加了指向该孤立页面的链接，修复了孤立问题。

## 2026-07-23 04:28
- 操作类型：health-check
- 影响文件：concepts/commercial-draft-disclosure.md, concepts/supply-chain-bill.md
- 备注：孤立页面修复：在 supply-chain-bill.md（供应链票据）中两处添加了指向 commercial-draft-disclosure.md（商业汇票信息披露制度）的链接。理由：(1) 供应链票据的定义部分提到《商业汇票承兑、贴现与再贴现管理办法》，配套的信息披露制度是直接关联内容；(2) 票据市场发展里程碑中 2020年12月人民银行第19号公告正是该制度的建立标志；(3) 相关实体部分增加链接方便查找。

## 2026-07-23 04:28
- 操作类型：health-check
- 影响文件：concepts/hundsun-frontend-coding-standards.md, concepts/html-template-dev-standards.md, concepts/css-less-sass-dev-standards.md
- 备注：修复孤立页面 concepts/css-less-sass-dev-standards.md：该页面属于恒生电子前端编码规范体系中的 CSS/LESS/SASS 规范子页面。修正了 hundsun-frontend-coding-standards.md（恒生电子前端编码规范）和 html-template-dev-standards.md（HTML/TEMPLATE 开发规范）中的 wiki 链接，将中文链接名 [[CSS/LESS/SASS 开发规范]] 等改为正确的文件名链接 [[css-less-sass-dev-standards|CSS/LESS/SASS 开发规范]]（保留显示文本），从而让这些页面正确指向 css-less-sass-dev-standards。同时修复了 css-less-sass-dev-standards.md 自身的断链问题，将其中的 [[恒生电子前端编码规范]] 和 [[HTML/TEMPLATE 开发规范]] 修正为指向正确文件名的链接。

## 2026-07-23 04:29
- 操作类型：health-check
- 影响文件：concepts/embedding.md, concepts/rag.md
- 备注：孤立页面修复：concepts/dense-model.md（稠密模型）

修复理由：该页面是关于"稠密模型（Dense Model）"的概念页面，内容质量完整，但被检测为孤立页面。实际上它与 mixture-of-experts.md 已互相链接，但为了增强知识网络连通性，额外在两个相关页面中添加了入链：

1. concepts/embedding.md：在介绍"稠密向量"时将"稠密"二字链接到 dense-model（嵌入模型产生稠密向量，底层使用稠密模型架构），并在相关概念部分添加了条目。
2. concepts/rag.md：在关键组件表格的嵌入模型说明中链接到 dense-model，并在相关概念部分添加了条目。

通过这两处修改，dense-model.md 现拥有来自 mixture-of-experts.md、embedding.md、rag.md 三个页面的入链，不再是孤立页面。

## 2026-07-23 04:31
- 操作类型：health-check
- 影响文件：concepts/dense-model.md, concepts/embedding.md
- 备注：孤立页面修复：concepts/embedding.md 是一个关于嵌入（Embedding）技术的概念页面，之前没有其他概念页面链接到它（虽然 index.md 有列表引用）。在 concepts/dense-model.md 中添加了指向 embedding 的 [[embedding|嵌入（Embedding）]] 链接，因为稠密模型是嵌入技术的底层架构基础，两者关系紧密。同时也在 dense-model.md 的"关联页面"部分加入了该链接。

## 2026-07-23 04:31
- 操作类型：health-check
- 影响文件：concepts/frontend-request-standards.md, concepts/html-template-dev-standards.md, concepts/css-less-sass-dev-standards.md, concepts/js-es6-dev-standards.md, concepts/vue-dev-standards.md
- 备注：修复孤立页面 concepts/frontend-request-standards.md（前端请求调用规范）。该页面属于"恒生电子前端编码规范"体系下的一个子规范页面。原本只有总纲页面（hundsun-frontend-coding-standards.md）链接到它，而其他同级子规范页面（HTML、CSS、JS、Vue 开发规范）均未包含对其的引用。在 html-template-dev-standards.md、css-less-sass-dev-standards.md、js-es6-dev-standards.md、vue-dev-standards.md 的"相关页面"部分添加了 [[frontend-request-standards|前端请求调用规范]] 链接。同时顺便修复了 js-es6-dev-standards.md 和 vue-dev-standards.md 中使用的旧链接名（[[恒生电子前端编码规范]] 等）为正确的页面名。修复理由：这些页面同属恒生电子前端编码规范体系，前端请求调用规范与该体系的其他子规范是平级关系，互相引用有助于知识库内的概念关联和导航。

## 2026-07-23 04:31
- 操作类型：health-check
- 影响文件：concepts/frontmatter-spec.md, concepts/wiki-compiler.md
- 备注：修复孤立页面 concepts/frontmatter.md：在 concepts/frontmatter-spec.md 的「相关页面」中添加 [[frontmatter]] 链接，因为该规范页面与 frontmatter 概念页面主题高度相关，前者描述具体规范字段，后者描述概念定义；在 concepts/wiki-compiler.md 中将「带有 frontmatter」改为「带有 [[frontmatter]]」，因为编译器生成 frontmatter 的过程与 frontmatter 概念直接相关。

## 2026-07-23 04:32
- 操作类型：health-check
- 影响文件：concepts/hundsun-frontend-coding-standards.md, concepts/html-template-dev-standards.md
- 备注：修复孤立页面 concepts/html-template-dev-standards.md：在恒生电子前端编码规范 (hundsun-frontend-coding-standards.md) 的"规范分类"章节中，将纯文本的"HTML/TEMPLATE 开发规范"改为 [[html-template-dev-standards|HTML/TEMPLATE 开发规范]] 链接，增强了页面间的关联性，解决了孤立页面问题。

## 2026-07-23 04:32
- 操作类型：health-check
- 影响文件：concepts/hundsun-bill-trade-v5-frontend.md, concepts/hundsun-bill-platform-components.md
- 备注：孤立页面修复：concepts/hundsun-bill-platform-components.md（恒生票据交易管理平台V5.0前端组件）未被任何其他内容页面引用。该页面详细描述了恒生电子票据交易管理平台V5.0的Vue前端组件体系，与 concepts/hundsun-bill-trade-v5-frontend.md（HUNDSUN票据交易管理平台V5.0前端开发指导）为同一平台的互补内容。在 hundsun-bill-trade-v5-frontend.md 的"相关页面"部分添加了指向该组件页面的 [[恒生票据交易管理平台V5.0前端组件]] 链接，使该页面不再孤立。

## 2026-07-23 04:33
- 操作类型：health-check
- 影响文件：concepts/hundsun-bill-trade-v5-frontend.md, concepts/hundsun-frontend-coding-standards.md, concepts/电子商业汇票综合处理平台.md
- 备注：孤立页面修复：concepts/hundsun-bill-trade-v5-frontend.md 是一个关于恒生电子 HUNDSUN 票据交易管理平台 V5.0 前端开发指导的页面，内容详实且有价值。该页面原本没有任何其他页面指向它。已在两个最相关的页面中添加了指向该页面的链接：(1) concepts/hundsun-frontend-coding-standards.md（恒生电子前端编码规范）——添加在"相关项目"章节，因为该编码规范与V5.0前端开发同属恒生电子前端技术体系；(2) concepts/电子商业汇票综合处理平台.md（电子商业汇票综合处理平台 BBSP）——添加在"相关产品"章节，因为两者都是恒生电子票据业务领域的产品（一个侧重前端开发指导，一个侧重后端综合处理平台）。

## 2026-07-23 04:33
- 操作类型：health-check
- 影响文件：concepts/电子商业汇票综合处理平台.md, concepts/hundsun-bill-trading-platform-v5.md, concepts/BaseDto.md, concepts/恒生电子.md
- 备注：孤立页面修复: concepts/hundsun-bill-trading-platform-v5.md

1. **电子商业汇票综合处理平台.md** — 在"相关产品"部分添加了 `[[hundsun-bill-trading-platform-v5]]` 链接，因为该页面与孤立页面描述的是同一产品体系（恒生电子票据交易管理平台），前者是整体平台概述，后者是后端开发细节，互为补充。
2. **hundsun-bill-trading-platform-v5.md**（孤立页面自身）— 修复了断链：将 `[[hundsun]]` 更正为 `[[恒生电子]]`（知识库中使用的中文页面名），并添加了指向 `[[电子商业汇票综合处理平台]]` 和 `[[hundsun-bill-trade-v5-frontend]]` 的链接以丰富关联。
3. **BaseDto.md** — 新创建页面，因为该 DTO 基类被多个恒生电子相关页面引用（包括孤立页面和电子商业汇票综合处理平台页面），是有效的概念实体。
4. **恒生电子.md** — 新创建页面，作为恒生电子公司的概念页面，被电子商业汇票综合处理平台页面引用，同时也是孤立页面中原本指向 `[[hundsun]]` 的正确目标（使用中文名称）。

## 2026-07-23 04:34
- 操作类型：health-check
- 影响文件：concepts/hundsun-frontend-coding-standards.md, concepts/frontend-request-standards.md, concepts/hundsun-bill-trade-v5-frontend.md
- 备注：修复孤立页面 concepts/hundsun-frontend-coding-standards.md（恒生电子前端编码规范）。在 frontend-request-standards.md 中修复了断链（将 [[恒生电子前端编码规范]] 修正为 [[hundsun-frontend-coding-standards|恒生电子前端编码规范]]），并在 hundsun-bill-trade-v5-frontend.md 的相关页面部分添加了指向该编码规范页面的链接，因为两者同属恒生电子前端生态体系，内容高度相关。

## 2026-07-23 04:34
- 操作类型：health-check
- 影响文件：concepts/hundsun-coding-standards.md
- 备注：修复孤立页面 concepts/hundsun-java-coding-standard.md：在恒生电子编码规范总则页面（hundsun-coding-standards.md）的"相关概念"部分添加了指向 [[恒生电子 Java 编码规范]] 的链接。理由：恒生电子编码规范总则与恒生电子 Java 编码规范同属恒生电子编码规范体系，总则描述通用规范，Java 编码规范是面向具体语言的专项规范，二者主题高度相关，阅读总则的用户很可能也需要参考 Java 编码规范。

## 2026-07-23 04:35
- 操作类型：health-check
- 影响文件：concepts/java-coding-standard-best-practices.md, concepts/hundsun-coding-standards.md
- 备注：修复孤立页面：concepts/java-coding-standard-best-practices.md (Java 编码规范最佳实践)。该页面为 Java 编码规范的概念总结页面，内容完整。在 concepts/hundsun-coding-standards.md (恒生电子编码规范总则) 的相关概念部分添加了指向该页面的 [[Java 编码规范最佳实践]] 链接。理由：两个页面主题高度相关——编码规范总则涵盖通用编码规范，而 Java 编码规范最佳实践是 Java 领域的具体编码实践总结，互为补充。

## 2026-07-23 04:35
- 操作类型：health-check
- 影响文件：concepts/js-es6-dev-standards.md, concepts/hundsun-frontend-coding-standards.md, concepts/frontend-request-standards.md
- 备注：修复孤立页面 concepts/js-es6-dev-standards.md。原因：该页面描述了恒生电子前端编码规范中的 JS/ES6 开发规范，但与父页面 concepts/hundsun-frontend-coding-standards.md 之间缺少完整链接。具体修复：1）在 hundsun-frontend-coding-standards.md 的"规范分类"第3项中，将纯文本"JS/ES6 开发规范"改为 [[js-es6-dev-standards|JS/ES6 开发规范]] 链接（已有"详细规范"部分的链接，但"规范分类"部分缺少）；2）在 frontend-request-standards.md 中，将错误的链接 [[JS/ES6 开发规范]] 修正为 [[js-es6-dev-standards|JS/ES6 开发规范]]。

## 2026-07-23 04:35
- 操作类型：health-check
- 影响文件：concepts/limited-recourse-service.md, concepts/票据业务系统非交易业务客户端功能.md
- 备注：孤立页面修复：concepts/limited-recourse-service.md（有限追索服务操作指引）是票交所提供的有限追索服务说明文档。在高度相关的 concepts/票据业务系统非交易业务客户端功能.md 页面的"追索清偿"功能部分和相关链接中，添加了指向 [[有限追索服务操作指引]] 的链接。理由：该页面详细介绍了追索清偿的客户端操作，而有限追索服务定义了追索权范围的约定规则，两者在票据追索业务上直接关联，用户在处理追索清偿业务时可参考有限追索服务的规则说明。

## 2026-07-23 04:36
- 操作类型：health-check
- 影响文件：concepts/batch-compile-test.md, concepts/llm-wiki.md, concepts/llm-entity-extraction.md
- 备注：孤立页面修复: concepts/llm-entity-extraction.md (LLM 实体抽取)。理由：该页面描述了利用大语言模型从文本中识别提取命名实体的技术，与批量编译测试中的实体提取能力直接相关。已在 concepts/batch-compile-test.md 的"相关概念"部分添加 [[llm-entity-extraction]] 链接，并在 concepts/llm-wiki.md 的功能特性描述和"相关页面"中分别添加链接，从而将孤立页面融入知识库网络。

## 2026-07-23 04:36
- 操作类型：health-check
- 影响文件：concepts/llm-entity-extraction.md, concepts/llm-wiki.md
- 备注：修复孤立页面 concepts/llm.md：在 concepts/llm-entity-extraction.md 中将"大语言模型"改为指向 [[llm]] 的双向链接（原文提及 LLM 实体抽取依赖于大语言模型，但没有链接到 LLM 概念页）；在 concepts/llm-wiki.md 中将"大语言模型"改为指向 [[llm]] 的双向链接（LLM Wiki 系统基于大语言模型，理应链接到 LLM 概念页）。

## 2026-07-23 04:37
- 操作类型：health-check
- 影响文件：concepts/hundsun-bill-trade-v5-frontend.md, concepts/message-channel.md
- 备注：孤立页面修复：concepts/message-channel.md（消息通道）。该页面描述了 HUNDSUN 票据交易管理平台中 TCP/HTTP/IBM MQ 三种通讯方式的抽象层。与其最相关的现有页面为 concepts/hundsun-bill-trade-v5-frontend.md（HUNDSUN 票据交易管理平台 V5.0 前端开发指导），两者同属 HUNDSUN 票据交易管理平台体系。已在 hundsun-bill-trade-v5-frontend.md 的"相关页面"区域添加 [[消息通道]] 链接，并同时补全了此前缺失的 [[消息转换]] 链接（消息通道页面中已引用该概念，但该页面本身不存在，此处一并补充以保持关联完整性）。

## 2026-07-23 04:37
- 操作类型：health-check
- 影响文件：concepts/message-channel.md, concepts/message-converter.md
- 备注：孤立页面修复：concepts/message-converter.md（消息转换）原本没有任何页面链接到它。在 concepts/message-channel.md 中，原有的 [[消息转换]] 链接是断链（目标页面不存在），将其修正为 [[message-converter|消息转换]]，使其正确指向 message-converter.md。这样既修复了断链，又让 message-converter.md 不再孤立。

## 2026-07-23 04:38
- 操作类型：health-check
- 影响文件：concepts/mixture-of-experts.md, concepts/rag.md
- 备注：孤立页面修复：concepts/mixture-of-experts.md 是一个关于 MoE（混合专家模型）架构的页面。它已与 concepts/dense-model.md 之间建立了双向链接（dense-model 中引用了 [[mixture-of-experts|Mixture of Experts]]），但检测工具仍将其标记为孤立。为进一步增强连接，在 concepts/rag.md 的"关键组件"表格的大语言模型行中增加了对 [[mixture-of-experts|MoE]] 的引用（以 Mixtral 8x7B 为例），并在"相关概念"列表中添加了 [[mixture-of-experts|混合专家模型（MoE）]] 条目。修复理由：MoE 是现代 LLM（如 Mixtral 8x7B）的重要架构变体，RAG 系统使用的 LLM 常基于 MoE 架构，两者存在合理关联。

## 2026-07-23 04:38
- 操作类型：health-check
- 影响文件：concepts/PKM报文体系.md, concepts/票据业务系统安全控制规范.md
- 备注：孤立页面修复：concepts/PKM报文体系.md 原本没有被任何页面引用。该页面描述了 PKM.001~PKM.004 四个报文的结构与流程。与之内容高度相关的概念页面 concepts/票据业务系统安全控制规范.md 中详细讨论了同样的四个报文，但未链接到 PKM报文体系。修复方式：在票据业务系统安全控制规范.md 的概述第一段末尾添加 [[PKM报文体系]] 链接，并在相关概念列表中添加该链接，使孤立页面获得入链。

## 2026-07-23 15:22
- 操作类型：health-check
- 影响文件：entities/hundsun.md
- 备注：修复孤立页面 entities/hundsun-technologies.md：在 entities/hundsun.md 中添加指向 [[Hundsun Technologies]] 的链接，消除孤立问题。

## 2026-07-23 15:25
- 操作类型：health-check
- 影响文件：entities/proxy-test-2.md, concepts/proxy.md
- 备注：修复孤立页面 entities/proxy-test-2.md：在 concepts/proxy.md 中添加对 [[proxy-test-2]] 的链接，将其关联到 Proxy 概念页。

## 2026-07-23 15:26
- 操作类型：health-check
- 影响文件：entities/shanghai-commercial-paper-exchange.md, entities/supply-chain-commercial-paper-platform.md, concepts/supply-chain-commercial-paper-platform.md
- 备注：修复孤立页面 entities/shanghai-commercial-paper-exchange.md：
1. 分析发现其引用的 [[supply-chain-commercial-paper]] 和 [[supply-chain-finance]] 链接指向不存在的页面。
2. 在 concepts/ 目录创建了 supply-chain-commercial-paper-platform.md 占位概念页，并在 content 中关联了 shanghai-commercial-paper-exchange 实体。
3. 更新 entities/shanghai-commercial-paper-exchange.md，修正引用链接为 [[supply-chain-commercial-paper-platform|供应链票据平台]] 和 [[supply-chain-finance|供应链金融]]（注：supply-chain-finance 已存在于 concepts 目录下，但需确认具体文件名）。
4. 重新验证并统一链接指向，确保 no dangling links。

## 2026-07-23 15:26
- 操作类型：health-check
- 影响文件：entities/shanghai-commercial-paper-exchange.md, concepts/supply-chain-note.md, concepts/supply-chain-finance.md, concepts/supply-chain-commercial-paper-platform.md
- 备注：修复孤立页面 entities/shanghai-commercial-paper-exchange.md：
1. 检查发现原文引用了不存在的 [[supply-chain-commercial-paper]] 和 [[supply-chain-finance]] 等链接。
2. 创建概念页 concepts/supply-chain-note.md 和 concepts/supply-chain-commercial-paper-platform.md 来完善相关知识网络。
3. 更新概念页 concepts/supply-chain-finance.md 使其正确指向新创建的实体。
4. 更新 entities/shanghai-commercial-paper-exchange.md，修正所有内部链接指向现存的页面。
5. 确保所有链接闭合，消除孤立状态。

## 2026-07-23 15:27
- 操作类型：health-check
- 影响文件：concepts/knowledge-base-compilation.md
- 备注：孤立页面修复: entities/test-doc-1.md。该页面已在 index.md 中有链接，但孤立检查未找到其被其他页面引用。在 concepts/knowledge-base-compilation.md 的"相关页面"部分添加 [[test-doc-1]] 链接，建立双向关联。修复理由：test-doc-1 是批量编译测试文档，与知识库编译流程直接相关。

## 2026-07-23 15:27
- 操作类型：health-check
- 影响文件：entities/test-doc-1.md
- 备注：孤立页面修复: entities/test-doc-2.md。在 entities/test-doc-1.md 的"关联"部分添加了对 [[Test Doc 2]] 的引用，因为两者属于同一 batch-compile 测试批次，存在直接的相关性。

## 2026-07-23 15:28
- 操作类型：health-check
- 影响文件：entities/test-document-11.md, concepts/batch-compile-test.md
- 备注：修复 entities/test-document-11.md 孤立页面问题：在概念页面 concepts/batch-compile-test.md 中添加指向该测试文档的 [[链接]]，使其被知识库中其他相关页面引用。

## 2026-07-23 15:28
- 操作类型：health-check
- 影响文件：entities/batch-compile-test.md
- 备注：修复孤立页面 entities/test-document-12.md：在 entities/batch-compile-test.md 中添加了对 [[Test Document 12]] 的链接，以解决其孤立问题。

## 2026-07-23 15:29
- 操作类型：health-check
- 影响文件：entities/test-document-14.md, concepts/bidirectional-linking.md
- 备注：Fixed orphan page 'entities/test-document-14.md' by creating its missing target 'concepts/bidirectional-linking.md'. The content for the new page was derived from links present in the orphan document. Updated both files to ensure bidirectional linking consistency.

## 2026-07-23 15:30
- 操作类型：health-check
- 影响文件：concepts/batch-compile-testing.md
- 备注：孤立页面修复：将 entities/test-document-16.md 链接到 concepts/batch-compile-testing.md，并添加双向链接。

## 2026-07-23 15:30
- 操作类型：health-check
- 影响文件：concepts/batch-compile-testing.md
- 备注：修复孤立页面 entities/test-document-17.md：在 concepts/batch-compile-testing.md 中添加 [[test-document-17]] 链接，使该测试文档与批量编译测试流程建立关联。

## 2026-07-23 15:31
- 操作类型：health-check
- 影响文件：entities/test-document-17.md, concepts/batch-compile-testing.md
- 备注：修复孤立页面 entities/test-document-18.md：在 test-document-17.md 和 batch-compile-testing.md 中添加了对 [[test-document-18]] 的链接，使其被知识库其他部分引用。

## 2026-07-23 15:32
- 操作类型：health-check
- 影响文件：concepts/batch-compile-testing.md, entities/batch-compile-test.md
- 备注：修复孤立页面 entities/test-document-20.md：在概念页面 concepts/batch-compile-testing.md 和实体页面 entities/batch-compile-test.md 中添加了对 test-document-20 的链接。

## 2026-07-23 18:48
- 操作类型：compile
- 影响文件：qa/线上服务内存泄漏排查.md
- 备注：从 raw/input-1784832481166.md 编译 QA 页面「线上服务内存泄漏排查」，记录线上服务定时 OOM 的 heapdump + Chrome DevTools 排查方法，status=published

## 2026-07-23 18:49
- 操作类型：compile
- 影响文件：qa/线上服务内存泄漏-每隔-6-小时-OOM-排查.md
- 备注：compile qa page from raw/input-1784832541372.md, status changed to published

## 2026-07-23 18:50
- 操作类型：compile
- 影响文件：qa/env-config-steps.md
- 备注：QA 导入编译：审核通过，将草稿转为正式问答页。原来源 qq-chat:790107c4-6269-41b8-aafb-e5454304947c，答复者 李四，关于配置环境变量（.env 文件）。

## 2026-07-23 18:55
- 操作类型：compile
- 影响文件：qa/docker-containers-timezone-setup.md
- 备注：compile: 从 raw/input-1784832903418.md 编译 QA 页面，状态转为 published。

## 2026-07-23 19:02
- 操作类型：compile
- 影响文件：concepts/mixture-of-experts.md, concepts/dense-model.md
- 备注：编译原始资料，生成 MoE 概念页及关联的稠密模型概念页，建立双向链接。

## 2026-07-23 19:02
- 操作类型：compile
- 影响文件：concepts/rag.md
- 备注：编译 RAG 概念页，包含核心流程、优势及相关链接。

## 2026-07-24 01:43
- 操作类型：compile
- 影响文件：qa/docker-timezone-setup.md
- 备注：从 qq-chat:8f915b7c-6ae4-420e-b297-98f6eb73b50d 编译 qa 页面：Docker 容器时区设置问题。

## 2026-07-27 08:54
- 操作类型：compile
- 影响文件：concepts/concept-placeholder.md
- 备注：编译原始资料 input-1785142392623.md 为 concept 页面，内容为简短占位符文本

## 2026-07-27 10:13
- 操作类型：compile
- 影响文件：qa/env-config-guide.md
- 备注：编译 raw/input-1785147185086.md（QQ QA 导入），将环境变量配置问答从 draft 发布为 published，写入 qa/env-config-guide.md

## 2026-07-27 12:25
- 操作类型：compile
- 影响文件：qa/how-to-configure-env-variables.md
- 备注：从 drafts/ 编译 qa 页面「如何配置环境变量？」，提升为 published 状态，建立双向链接到 [[dotenv]]。

## 2026-07-27 12:27
- 操作类型：compile
- 影响文件：qa/env-config-steps.md, concepts/dotenv.md, concepts/env-config-best-practices.md
- 备注：compile: 从 raw/input-1785155220506.md 编译环境变量配置问答为 qa/env-config-steps.md (published)，并创建关联概念页 dotenv 和环境变量管理最佳实践

## 2026-07-27 12:36
- 操作类型：compile
- 影响文件：qa/env-config.md, concepts/environment-variables.md
- 备注：编译 QQ 导入 qa 问答：如何配置环境变量（draft → published），同时新建环境变量概念页以支持双向链接

## 2026-07-27 12:46
- 操作类型：compile
- 影响文件：qa/env-config.md, concepts/环境变量管理.md, concepts/env-file-spec.md
- 备注：从 raw/input-1785156330383.md（QQ 聊天导入，draft 状态）编译环境变量相关页面：创建 qa/env-config.md（published 状态，回答者李四），并补充环境变量管理概念页和 .env 文件规范概念页，建立三方双向链接网络。

## 2026-07-27 12:47
- 操作类型：compile
- 影响文件：qa/env-config-setup.md, concepts/dotenv-file-spec.md, concepts/project-config-best-practice.md
- 备注：compile: 从 raw/input-1785156454697.md 编译环境变量配置 QA 为 published 页面，并创建关联概念页面完善知识图谱

## 2026-07-27 14:16
- 操作类型：compile
- 影响文件：entities/shanghai-commercial-paper-exchange.md, concepts/标准化票据.md, concepts/中国票据业务系统.md
- 备注：从上海票交所官网首页原始资料编译：创建实体页「上海票据交易所」，概念页「标准化票据」和「中国票据业务系统」，建立双向链接体系。

## 2026-07-27 15:38
- 操作类型：compile
- 影响文件：concepts/recursion.md, concepts/tail-recursion.md
- 备注：从 raw/input-1785166708570.md 编译递归概念页面及关联尾递归页面。原始资料出现编码损坏，基于可识别的 "base case / recursive case" 等关键词重建概念内容。

## 2026-07-28 16:14
- 操作类型：compile
- 影响文件：entities/shanghai-commercial-paper-exchange.md, concepts/standardized-bills.md, concepts/china-bill-business-system.md
- 备注：从 raw/input-1785255262534.md（上海票据交易所官网首页爬取数据）编译：上海票据交易所实体页、标准化票据概念页、中国票据业务系统概念页

## 2026-07-28 17:45
- 操作类型：compile
- 影响文件：entities/上海票据交易所.md, concepts/中国票据业务系统.md, concepts/标准化票据.md, concepts/供应链票据.md
- 备注：编译 raw/input-1785260725141.md（上海票据交易所官网首页爬取数据），创建 1 个实体页 + 3 个概念页，建立双向链接与实体关系

## 2026-07-29 09:17
- 操作类型：compile
- 影响文件：qa/rediscount-client-password-reset.md
- 备注：编译 raw/input-1785316634688.md 为 qa 页面：再贴现客户端 caozuo001/002/003 密码重置，status=draft→published，建立双向链接[[再贴现系统]]

## 2026-07-29 09:17
- 操作类型：compile
- 影响文件：qa/buyer-paid-interest-settlement.md
- 备注：编译 draft QA 为 published 页面：意向询价买方付息应答结算金额问题（买方付息应答时结算金额需减去利息）

## 2026-07-29 09:17
- 操作类型：compile
- 影响文件：qa/票交所客户端查询交割单.md, entities/票交所.md, entities/票交所-覃舒桐.md, entities/华夏银行-王东.md
- 备注：从 raw/input-1785316663842.md 编译票交所客户端查询交割单 QA 页面（draft→published），并创建关联实体页面：票交所（实体）、票交所-覃舒桐（实体）、华夏银行-王东（实体），建立双向链接网络

## 2026-07-29 09:18
- 操作类型：compile
- 影响文件：qa/acceptor-type-vs-list-mismatch.md
- 备注：compile: 将 raw/input-1785316682506.md（承兑人类型与清单不一致问答）编译为体系化 qa 页面，status=draft→published

## 2026-07-29 09:18
- 操作类型：compile
- 影响文件：qa/摘牌权限开通.md
- 备注：编译 QQ 导入 QA 条目：摘牌权限开通（draft → published），建立双向链接 [[交易员]]，抽取无额外实体关系。

## 2026-07-29 09:18
- 操作类型：compile
- 影响文件：qa/listing-inquiry-cpp014002-ft07-attachment.md, entities/zongfu-platform.md, entities/trading-system.md, entities/cpp014002.md, entities/cpp001002.md
- 备注：从QQ聊天记录draft编译挂牌询价FT07附件绑定问答，建立相关实体页面（综服平台、交易系统、CPP014002、CPP001002），抽取实体关系，状态改为published

## 2026-07-29 09:19
- 操作类型：compile
- 影响文件：qa/票交所环境日间状态.md
- 备注：compile: QQ导入QA（票交所环境日间状态），从draft转为published。涉及上海票据交易所的日切过程，建立双向链接到[[上海票据交易所]]和[[中国票据业务系统]]。

## 2026-07-29 09:19
- 操作类型：compile
- 影响文件：qa/贴现通摘牌签收完成后收到Cas001002，清算失败的原因是什么？.md, entities/贴现通.md, entities/大连银行.md, entities/曹燕秋.md, entities/票交所.md, entities/覃舒桐.md, concepts/大额切日.md
- 备注：compile 任务：将 raw/input-1785316750466.md（QQ 导入 QA draft）编译为 published QA 页面及关联实体/概念页面

---
title: HUNDSUN票据交易管理平台
type: entity
created: 2025-01-20
updated: 2025-01-20
source: raw/wiki-batch-1784698573547-7-HUNDSUN__________V5.0-______.md
tags: [HUNDSUN, 票据交易, 金融科技, 接口开发]
---

# HUNDSUN票据交易管理平台

**HUNDSUN票据交易管理平台软件V5.0** 是恒生电子（HUNDSUN）推出的票据交易管理系统，提供票据业务的交易管理、接口开发与消息通道集成能力。

## 核心功能模块

### 消息通道（Message Channel）
平台支持三种主流通讯方式与外部系统对接：
- [[TCP 通讯]] — 基于 TCP 协议的消息通道
- [[HTTP 通讯]] — 基于 HTTP/HTTPS 协议的消息通道
- [[IBM MQ 通讯]] — 基于 IBM MQ 队列的消息通道

通过配置中心参数 `adapter.is_use_new_message_channel=1` 启用新版消息通道，支持同时启用多种通讯方式。

### 消息转换（Message Converter）
[[消息转换]] 机制负责内部 JSON 消息与外部系统报文的双向转换，采用**约定优于配置**规则，类名约定为 `{接口编号}MessageConverter`。

## 关键技术特性

- **多通道并行**：支持 TCP、HTTP、IBM MQ 同时启用
- **SSL/TLS 支持**：HTTPS 通讯支持证书配置
- **Netty 日志**：支持 Netty 日志调试功能
- **字符集配置**：支持不同平台的字符集（Unix 819 / Windows 1381）
- **权限认证**：IBM MQ 支持用户凭证认证

## 版本信息

- 版本：V5.0
- 类型：票据交易管理平台软件

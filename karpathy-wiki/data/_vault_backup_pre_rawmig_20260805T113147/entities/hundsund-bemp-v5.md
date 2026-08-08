---
title: 恒生票据管理系统 BEMP V5.0
type: entity
created: 2025-03-30
updated: 2025-03-30
source: raw/wiki-batch-1784698415451-3-HUNDSUN__________V5.0-_ORACLE_______-20220706.md
tags: [恒生电子, 票据管理, BEMP, Oracle, V5.0]
---

# 恒生票据管理系统 BEMP V5.0

## 概述

**恒生票据管理系统 BEMP V5.0**（英文缩写 **BEMP**，项目编号 20180048）是恒生电子股份有限公司开发的企业级票据交易管理平台，基于 Oracle 数据库运行。本系统是 **[[票据交易管理平台]]** 领域的核心产品，提供票据全生命周期管理功能。

## 基本信息

| 属性 | 值 |
|------|-----|
| 产品名称 | 票据管理系统 |
| 英文缩写 | BEMP |
| 版本号 | V5.0 |
| 项目编号 | 20180048 |
| 数据库平台 | Oracle |
| 开发者 | 恒生电子股份有限公司 |
| 文档类型 | 概要设计说明书 |

## 版本历史

该系统经历了多个迭代版本，包括 V5.0.2 至 V5.0.15 等子版本。主要涉及的数据对象修改覆盖交易信息、背书信息、企业交易、票据评估等多个模块。

### 主要版本节点

| 版本 | 修改对象举例 | 说明 |
|-----|-------------|------|
| V5.0.15 | tb_trans_info_appl | 最新版本修订 |
| V5.0.10 | tb_bill_info_ass | 刘翔提交修订 |
| V5.0.6 | tm_asset_valuate_info | 杨奎提交修订 |
| V5.0.3 | tm_asset_valuate_detail, te_pl_pre_agreement 等 | 大规模修订 |
| V5.0.2 | 多个 te_std_* 基础表 | 早期基础版本 |

## 核心数据对象

系统涉及大量数据库表对象，按前缀可分为以下几类：

### 交易信息类（tb_*）
- tb_trans_info_appl — 交易信息申请表
- tb_trans_info_sign — 交易信息签收表
- tb_trans_ass_info — 交易关联信息表
- tb_trans_sts_change — 交易状态变更表
- tb_ban_endrsmt_info — 背书信息表
- tb_bill_info_ass — 票据信息关联表
- tb_corp_trans_info — 企业交易信息表

### 标准产品类（te_std_*）
- te_std_prsttn_bill — 标准票据表
- te_std_corp_dpst_bill — 企业存款票据
- te_std_recourse_bill — 追索票据
- te_std_creation — 票据创建
- te_std_counter_acct — 对手账户

### 票据交易类（te_pl_*）
- te_pl_disc_appl — 贴现申请表
- te_pl_pre_agreement — 预签协议
- te_pl_stock_book_his — 库存账簿历史

### 风险与参数类（tm_*）
- tm_risk_company_white_roll — 风险企业白名单
- tm_asset_valuate_info — 资产估值信息
- tm_asset_valuate_detail — 资产估值明细
- tm_cpes_member_param — CPES 成员参数
- tm_cpes_scb_mapping — CPES SCB 映射

### 其他业务表（te_ce_*, te_pb_*）
- te_ce_reserve_register — 准备金登记
- te_ce_facpt_sign_info — 授信签约信息
- te_pb_guarntr_bill — 保函票据
- te_pb_impawn_batch — 质押批次

## 相关概念

- [[票据交易管理平台]] — 票据交易管理领域概念
- [[恒生电子]] — 系统开发企业
- [[BEMP 数据库表结构]] — 系统的数据库元数据

## 参考资料

- 恒生电子股份有限公司.《票据管理系统V5.0 概要设计说明书》（Oracle版）, 2022.

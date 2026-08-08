---
title: 交易系统
type: entity
created: 2026-07-29T00:00:00.000Z
updated: 2026-07-29T00:00:00.000Z
source: 'qq-chat:5f1bd3b1-b799-470d-9c13-2be3d3667480'
tags:
  - 票交所
  - 系统
entities:
  - name: 综服平台
    relation: related_to
  - name: CPP014002
    relation: related_to
  - name: CPP001002
    relation: related_to
---
## 概述

[[交易系统]]是票交所的核心业务系统。与[[综服平台]]不同，交易系统在挂牌询价携带附件等操作上有独立的规则约束。

## 相关规则

- 挂牌询价 [[CPP014002]] 携带 FT07 附件时，在交易系统中仍需要通过 [[CPP001002]] 绑定

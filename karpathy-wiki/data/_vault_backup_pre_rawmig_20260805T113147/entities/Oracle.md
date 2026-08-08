---
title: Oracle
type: entity
created: 2025-01-21
updated: 2025-01-21
source: 恒生电子《数据库编码规范》
tags: [数据库, Oracle, 关系型数据库]
---

# Oracle

Oracle Database 是一种企业级关系型数据库管理系统，在 [[hundsun-db-coding-standards|恒生电子数据库编码规范]] 中被列为两大目标数据库之一。

## 编码规范要点

- 原生支持 PL/SQL 和事务
- 使用 `SEQUENCE` 对象实现自增
- 分页查询使用 `ROWNUM` 或 `FETCH FIRST` 语法
- 脚本使用 `CREATE OR REPLACE PROCEDURE` 语法
- 异常处理使用 `EXCEPTION` 块

## 相关页面

- [[hundsun-db-coding-standards]]
- [[MySQL]]
- [[mysql-vs-oracle-coding-practices]]

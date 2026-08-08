---
title: MySQL
type: entity
created: 2025-01-21
updated: 2025-01-21
source: 恒生电子《数据库编码规范》
tags: [数据库, MySQL, 关系型数据库]
---

# MySQL

MySQL 是一种流行的开源关系型数据库管理系统，在 [[hundsun-db-coding-standards|恒生电子数据库编码规范]] 中被列为两大目标数据库之一。

## 编码规范要点

- 存储引擎推荐使用 **InnoDB**（支持事务、行级锁）
- 支持 `AUTO_INCREMENT` 自增列
- 分页查询使用 `LIMIT … OFFSET …`
- 脚本使用 `DELIMITER` 和 `CREATE PROCEDURE` 语法

## 相关页面

- [[hundsun-db-coding-standards]]
- [[Oracle]]
- [[mysql-vs-oracle-coding-practices]]

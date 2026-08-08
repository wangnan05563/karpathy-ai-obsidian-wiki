---
title: Docker
type: entity
created: 2026-07-24
updated: 2026-07-24
source: qq-chat:673f40bc-f6ae-4263-a7eb-2e6a6286e570
tags: [Docker, 容器, 部署]
---

# Docker

Docker 是一种主流的容器化平台，通过镜像与容器机制实现应用的标准化打包与分发，广泛应用于开发、测试与生产部署场景。

## 关键特性

- 通过 **镜像（Image）** 与 **容器（Container）** 实现应用隔离
- 支持多发行版基础镜像（Alpine、Debian 等）
- 通过环境变量（如 `TZ`）配置容器运行时行为

## 常见配置要点

- 时区设置：仅设置 `TZ` 环境变量往往不够，还需在镜像中安装 `tzdata` 包
  - Alpine 镜像：`apk add tzdata`
  - Debian 镜像：`apt-get install tzdata`

## 相关页面

- [[docker-containers-timezone-setup]]
- [[docker-timezone-setup]]
- [[容器]]

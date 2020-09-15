# QCloud_DDNS_IPv6

## 这是啥？ What's this?

一个用来将本机IPv6地址同步到腾讯云域名解析服务的Python脚本，实现DDNS功能。

A Python script to sync local IPv6 address to QCloud Domain Resolution Service, implement DDNS function.

## 依赖 Dependence

- 能够网络访问腾讯云（走IPv4） / Network access to QCloud(Generally, through IPv4)

- 一个可用的IPv6地址 / An available IPv6 address

- python==3

- requests==any

## 部署 Deployment

### 1

在腾讯云申请你的API密钥（SECRETID和SECRETKEY）
Apply for your API keys (SECRETID and SECRETKEY) on QCloud

https://console.cloud.tencent.com/cam/capi

### 2

修改main.py中每一个注释了CHANGEME的行（CTRL+F）

Modify every line commented with "CHANGEME" in main.py(CTRL+F)

### 3

将脚本加入计划任务，每隔1~5分钟执行一次
Add the script to the scheduled task and execute it every 1 to 5 minutes

Windows：在开始菜单中搜索“任务计划程序”
Windows：search "task" in start menu

Linux：crontab

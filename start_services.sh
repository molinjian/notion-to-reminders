#!/bin/bash


chmod +x sync.py
chmod +x reverse_sync.py

# 复制 plist 文件到 LaunchAgents 目录
cp com.user.notion-to-reminders.plist ~/Library/LaunchAgents/
cp com.user.notion-to-reminders-reverse.plist ~/Library/LaunchAgents/

# 设置文件权限
chmod 644 ~/Library/LaunchAgents/com.user.notion-to-reminders.plist
chmod 644 ~/Library/LaunchAgents/com.user.notion-to-reminders-reverse.plist

# 加载服务
echo "正在启动正向同步服务..."
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.notion-to-reminders.plist

echo "正在启动反向同步服务..."
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.notion-to-reminders-reverse.plist

# 检查服务状态
echo -e "\n服务状态："
echo "正向同步服务："
launchctl list | grep notion-to-reminders

echo -e "\n反向同步服务："
launchctl list | grep notion-to-reminders-reverse

echo -e "\n启动完成！"
echo "日志文件："
echo "- 正向同步日志：sync.log"
echo "- 正向同步错误日志：sync_error.log"
echo "- 反向同步日志：reverse_sync.log"
echo "- 反向同步错误日志：reverse_sync_error.log" 

#!/bin/bash

# 停止服务
echo "正在停止正向同步服务..."
launchctl bootout gui/$(id -u)/com.user.notion-to-reminders

echo "正在停止反向同步服务..."
launchctl bootout gui/$(id -u)/com.user.notion-to-reminders-reverse

# 检查服务状态
echo -e "\n服务状态："
echo "正向同步服务："
launchctl list | grep notion-to-reminders

echo -e "\n反向同步服务："
launchctl list | grep notion-to-reminders-reverse

echo -e "\n停止完成！"
echo "如果需要重新启动服务，请运行 ./start_services.sh" 
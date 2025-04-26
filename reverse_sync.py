#!/usr/bin/env python3
"""
Notion to Apple Reminders Reverse Sync Script
This script synchronizes completed tasks from Apple Reminders back to Notion.
"""

import os
import json
import subprocess
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz

# Load environment variables
load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
REMINDERS_LIST = os.getenv("REMINDERS_LIST_NAME", "提醒事项测试")

# Notion API 配置
NOTION_VERSION = "2022-06-28"
NOTION_API_URL = "https://api.notion.com/v1"

# 设置时区为北京时间
beijing_tz = pytz.timezone('Asia/Shanghai')

# 获取今天的日期（北京时间）
today = datetime.now(beijing_tz).strftime("%Y-%m-%d")

def run_applescript(script):
    """Execute AppleScript command"""
    try:
        process = subprocess.run(['osascript', '-e', script], 
                               capture_output=True, 
                               text=True, 
                               check=True)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"执行 AppleScript 失败: {e}")
        print(f"错误输出: {e.stderr}")
        if "not authorized" in e.stderr or "不允许发送事件" in e.stderr:
            print("\n***\n请检查 系统偏好设置 > 安全性与隐私 > 隐私 > 自动化，\n确保你的终端或 Python 有权限控制 '提醒事项' App。\n***\n")
        return None
    except FileNotFoundError:
        print("错误：找不到 'osascript' 命令。请确保你在 macOS 上运行。")
        return None

def get_completed_reminders(list_name):
    """Get all completed reminders in the specified list"""
    script = f'''
    tell application "Reminders"
        set reminder_names to {{}}
        if exists list "{list_name}" then
            tell list "{list_name}"
                set reminder_names to name of every reminder whose completed is true
            end tell
        end if
        return reminder_names
    end tell
    '''
    output = run_applescript(script)
    if output:
        return [name.strip() for name in output.split(',') if name.strip()]
    return []

def get_notion_page_by_title(title):
    """Search for a Notion page by title"""
    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }

        # 构建查询条件
        query_url = f"{NOTION_API_URL}/databases/{DATABASE_ID}/query"
        query_data = {
            "filter": {
                "property": "任务名称",
                "title": {
                    "equals": title
                }
            }
        }

        response = requests.post(query_url, headers=headers, json=query_data)
        
        if response.status_code != 200:
            print(f"查询任务失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
        results = response.json().get("results", [])
        if results:
            return results[0]  # 返回第一个匹配的结果
        return None

    except Exception as e:
        print(f"从 Notion 获取数据失败: {e}")
        return None

def update_notion_page_status(page_id, status="完成"):
    """Update the status of a Notion page"""
    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }

        update_url = f"{NOTION_API_URL}/pages/{page_id}"
        update_data = {
            "properties": {
                "状态": {
                    "status": {
                        "name": status
                    }
                }
            }
        }

        response = requests.patch(update_url, headers=headers, json=update_data)
        
        if response.status_code != 200:
            print(f"更新任务状态失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
        return True

    except Exception as e:
        print(f"更新 Notion 页面状态失败: {e}")
        return False

def sync_reminders_to_notion():
    """Main synchronization function"""
    print("开始同步 Reminders 到 Notion...")
    
    # 获取已完成的提醒事项
    completed_reminders = get_completed_reminders(REMINDERS_LIST)
    print(f"列表 '{REMINDERS_LIST}' 中已完成提醒: {len(completed_reminders)} 个")
    
    if not completed_reminders:
        print("没有找到已完成的提醒事项。")
        return

    updated_count = 0
    not_found_count = 0

    for reminder_title in completed_reminders:
        print(f"\n处理提醒: '{reminder_title}'")
        
        # 在 Notion 中查找对应的页面
        page = get_notion_page_by_title(reminder_title)
        
        if page:
            # 更新页面状态
            if update_notion_page_status(page["id"]):
                print(f"成功更新任务状态: '{reminder_title}'")
                updated_count += 1
            else:
                print(f"更新任务状态失败: '{reminder_title}'")
        else:
            print(f"未找到对应的 Notion 任务: '{reminder_title}'")
            not_found_count += 1

    print(f"\n同步完成。成功更新了 {updated_count} 个任务，未找到 {not_found_count} 个任务。")

if __name__ == "__main__":
    sync_reminders_to_notion() 
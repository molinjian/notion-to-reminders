#!/usr/bin/env python3
"""
Notion to Apple Reminders Sync Script
This script synchronizes tasks from a Notion database to Apple Reminders.
"""

import os
import json
import subprocess
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
REMINDERS_LIST = os.getenv("REMINDERS_LIST_NAME", "个人提醒")

# Notion API 配置
NOTION_VERSION = "2022-06-28"
NOTION_API_URL = "https://api.notion.com/v1"

# 获取今天的日期（UTC时间）
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

if not NOTION_TOKEN or not DATABASE_ID:
    print("错误：请确保在 .env 文件中设置了 NOTION_TOKEN 和 NOTION_DATABASE_ID")
    exit(1)

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

def get_existing_reminders(list_name):
    """Get all existing reminders in the specified list"""
    script = f'''
    tell application "Reminders"
        set reminder_names to {{}}
        if exists list "{list_name}" then
            tell list "{list_name}"
                set reminder_names to name of every reminder whose completed is false
            end tell
        end if
        return reminder_names
    end tell
    '''
    output = run_applescript(script)
    if output:
        return [name.strip() for name in output.split(',') if name.strip()]
    return []

def add_reminder(title, list_name, due_date=None):
    """Add a new reminder to the specified list with optional due date"""
    escaped_title = title.replace('"', '\\"')
    script = f'''
    tell application "Reminders"
        if not (exists list "{list_name}") then
            make new list with properties {{name:"{list_name}"}}
        end if
        tell list "{list_name}"
            set newReminder to make new reminder with properties {{name:"{escaped_title}"}}
    '''
    
    if due_date:
        # 将日期字符串转换为 AppleScript 日期格式
        date_obj = datetime.strptime(due_date, "%Y-%m-%d")
        script += f'''
            set dueDate to current date
            set year of dueDate to {date_obj.year}
            set month of dueDate to {date_obj.month}
            set day of dueDate to {date_obj.day}
            set remind me date of newReminder to dueDate
    '''
    
    script += '''
        end tell
    end tell
    '''
    run_applescript(script)
    print(f"已添加提醒: '{title}' 到列表 '{list_name}'" + (f", 截止日期: {due_date}" if due_date else ""))

def get_notion_tasks():
    """Fetch tasks from Notion database using REST API"""
    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }

        # 先尝试获取数据库信息
        print("尝试获取数据库信息...")
        db_url = f"{NOTION_API_URL}/databases/{DATABASE_ID}"
        db_response = requests.get(db_url, headers=headers)
        
        if db_response.status_code != 200:
            print(f"获取数据库信息失败: {db_response.status_code}")
            print(f"错误信息: {db_response.text}")
            return None  # 返回 None 表示连接失败
            
        db_info = db_response.json()
        print(f"成功连接到数据库: {db_info.get('title', [{'plain_text': '未知'}])[0]['plain_text']}")

        # 构建查询条件
        query_url = f"{NOTION_API_URL}/databases/{DATABASE_ID}/query"
        query_data = {
            "filter": {
                "and": [
                    {
                        "or": [
                            {
                                "property": "状态",
                                "status": {
                                    "equals": "待办"
                                }
                            },
                            {
                                "property": "状态",
                                "status": {
                                    "equals": "里程碑"
                                }
                            }
                        ]
                    },
                    {
                        "property": "截止日期",
                        "date": {
                            "on_or_before": today
                        }
                    }
                ]
            },
            "page_size": 20
        }

        response = requests.post(query_url, headers=headers, json=query_data)
        
        if response.status_code != 200:
            print(f"查询任务失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None  # 返回 None 表示连接失败
            
        results = response.json().get("results", [])
        print(f"找到 {len(results)} 个任务")
        return results

    except Exception as e:
        print(f"从 Notion 获取数据失败: {e}")
        print("详细错误信息:")
        print(f"数据库 ID: {DATABASE_ID}")
        print(f"Token 前几位: {NOTION_TOKEN[:10]}...")
        return None  # 返回 None 表示连接失败

def sync_notion_to_reminders():
    """Main synchronization function"""
    print("开始同步 Notion 到 Reminders...")
    
    # 获取现有的提醒事项列表
    existing_reminders = get_existing_reminders(REMINDERS_LIST)
    print(f"列表 '{REMINDERS_LIST}' 中现有未完成提醒: {len(existing_reminders)} 个")
    
    notion_pages = get_notion_tasks()
    if notion_pages is None:  # 连接失败
        print("连接 Notion 失败，同步终止。")
        return

    # 获取 Notion 中的所有任务名称
    notion_titles = []
    if notion_pages:  # 如果有页面，处理页面内容
        print(f"从 Notion 获取到 {len(notion_pages)} 个页面。")
        for page in notion_pages:
            try:
                properties = page.get("properties", {})
                if "任务名称" in properties:
                    title_parts = properties["任务名称"].get("title", [])
                    task_title = "".join([part.get("plain_text", "") for part in title_parts])
                    if task_title:
                        # 获取截止日期
                        due_date = None
                        if "截止日期" in properties:
                            date_property = properties["截止日期"].get("date")
                            if date_property and date_property.get("start"):
                                due_date = date_property["start"]
                        
                        notion_titles.append((task_title, due_date))
            except Exception as e:
                page_id = page.get("id", "未知ID")
                print(f"处理页面 {page_id} 时出错: {e}")
    else:
        print("从 Notion 获取到 0 个页面。")

    added_count = 0
    skipped_count = 0
    deleted_count = 0

    # 删除不在 Notion 中的提醒事项
    for reminder in existing_reminders:
        if reminder not in [title for title, _ in notion_titles]:
            delete_reminder(reminder, REMINDERS_LIST)
            deleted_count += 1
            print(f"已删除提醒: '{reminder}'")

    # 如果列表为空，直接添加所有任务
    skip_check = len(existing_reminders) == 0

    if notion_pages:  # 如果有页面，添加新任务
        for page in notion_pages:
            try:
                properties = page.get("properties", {})
                
                # 获取任务名称
                task_title = None
                due_date = None
                if "任务名称" in properties:
                    title_parts = properties["任务名称"].get("title", [])
                    task_title = "".join([part.get("plain_text", "") for part in title_parts])
                
                # 获取截止日期
                if "截止日期" in properties:
                    date_property = properties["截止日期"].get("date")
                    if date_property and date_property.get("start"):
                        due_date = date_property["start"]
                
                if not task_title:
                    print(f"警告: 页面 {page['id']} 找不到任务名称，跳过。")
                    continue

                # 如果列表为空，直接添加；否则检查是否已存在
                if skip_check or task_title not in existing_reminders:
                    add_reminder(task_title, REMINDERS_LIST, due_date)
                    added_count += 1
                else:
                    skipped_count += 1
                    print(f"提醒 '{task_title}' 已存在，跳过。")

            except Exception as e:
                page_id = page.get("id", "未知ID")
                print(f"处理页面 {page_id} 时出错: {e}")

    print(f"同步完成。新增了 {added_count} 个提醒事项，跳过了 {skipped_count} 个已存在的提醒，删除了 {deleted_count} 个不存在的提醒。")

def delete_reminder(title, list_name):
    """Delete a reminder from the specified list"""
    escaped_title = title.replace('"', '\\"')
    script = f'''
    tell application "Reminders"
        if exists list "{list_name}" then
            tell list "{list_name}"
                set theReminders to (every reminder whose name is "{escaped_title}")
                repeat with theReminder in theReminders
                    delete theReminder
                end repeat
            end tell
        end if
    end tell
    '''
    run_applescript(script)

if __name__ == "__main__":
    sync_notion_to_reminders() 
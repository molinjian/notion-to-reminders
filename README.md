# Notion to Apple Reminders Sync

这个项目用于在 Notion 数据库和 Apple 提醒事项之间进行双向同步。

## 功能特点

- 自动同步 Notion 数据库中的任务到 Apple 提醒事项
- 自动同步 Apple 提醒事项中的任务到 Notion 数据库
- 支持自定义同步频率
- 支持选择目标提醒事项列表
- 自动跳过已存在的提醒事项
- 支持设置提醒事项的截止日期

## 安装要求

- Python 3.7+
- macOS 系统
- Notion 账户和数据库访问权限

## 安装步骤

1. 克隆项目到本地：
   ```bash
   git clone [your-repo-url]
   cd notion-to-reminders
   ```

2. 创建并激活虚拟环境：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   - 复制 `.env.example` 为 `.env`
   - 编辑 `.env` 文件，填入你的 Notion API Token 和数据库 ID

## 使用方法

### Notion 到 Reminders 同步
1. 手动运行同步：
   ```bash
   python sync.py
   ```

2. 设置自动同步：
   - 使用 crontab：
     ```bash
     crontab -e
     ```
     添加以下行（每小时同步一次）：
     ```
     0 * * * * /usr/bin/python3 /path/to/your/notion-to-reminders/sync.py >> /path/to/your/notion-to-reminders/sync.log 2>&1
     ```

   - 或使用 launchd（推荐）：
     ```bash
     cp com.user.notion-to-reminders.plist ~/Library/LaunchAgents/
     launchctl load ~/Library/LaunchAgents/com.user.notion-to-reminders.plist
     ```

### Reminders 到 Notion 同步
1. 手动运行同步：
   ```bash
   python reverse_sync.py
   ```

2. 设置自动同步：
   - 使用 crontab：
     ```bash
     crontab -e
     ```
     添加以下行（每小时同步一次）：
     ```
     30 * * * * /usr/bin/python3 /path/to/your/notion-to-reminders/reverse_sync.py >> /path/to/your/notion-to-reminders/reverse_sync.log 2>&1
     ```

   - 或使用 launchd（推荐）：
     ```bash
     cp com.user.notion-to-reminders-reverse.plist ~/Library/LaunchAgents/
     launchctl load ~/Library/LaunchAgents/com.user.notion-to-reminders-reverse.plist
     ```

## 配置说明

### Notion 配置
1. 创建 Notion Integration：
   - 访问 https://www.notion.so/my-integrations
   - 创建新的集成
   - 获取 Internal Integration Token

2. 分享数据库：
   - 打开你的 Notion 数据库
   - 点击右上角的 "..." 菜单
   - 选择 "Add connections"
   - 选择你创建的集成

### Apple Reminders 配置
- 首次运行时，系统会请求访问提醒事项的权限
- 确保在系统偏好设置中允许 Python 访问提醒事项

## 故障排除

1. 检查日志文件：
   - `sync.log`：Notion 到 Reminders 的标准输出日志
   - `sync_error.log`：Notion 到 Reminders 的错误日志
   - `reverse_sync.log`：Reminders 到 Notion 的标准输出日志
   - `reverse_sync_error.log`：Reminders 到 Notion 的错误日志

2. 常见问题：
   - 确保 `.env` 文件中的配置正确
   - 确保 Notion 数据库已正确分享给集成
   - 确保系统已授权 Python 访问提醒事项
   - 如果同步失败，检查日志文件中的具体错误信息

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License 
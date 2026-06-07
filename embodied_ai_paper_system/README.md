# 具身智能文献抓取与 Obsidian 内化系统

每日自动执行：

1. Semantic Scholar 检索近一年高影响论文及近 90 天前沿论文。
2. 从每周更新的本地基石论文库取候选。
3. 三个候选池独立评分，按 `6 + 5 + 4` 合并为 Top 15。
4. DeepSeek 选择综述/脉络、深度研究、系统应用各一篇。
5. PDF 只下载到 Obsidian Vault 的 `Attachments/Papers`。
6. 解析并生成 `Daily Embodied AI/YYYY-MM-DD_Daily_Embodied_AI.md`。

## 项目目录

```text
embodied_ai_paper_system/
├─ config/       # 关键词、运行配置、基石论文库
├─ data/         # 候选记录、缓存、推荐历史
├─ logs/         # 每日运行日志
├─ prompts/      # DeepSeek 筛选与解析提示词
├─ scripts/      # Windows 定时任务入口
├─ src/          # 核心代码
├─ tests/        # 离线测试
├─ .env.example  # 需要用户填写的配置模板
└─ main.py       # 命令行入口
```

Obsidian 内会自动创建：

```text
你的 Vault/
├─ Daily Embodied AI/
└─ Attachments/Papers/YYYY/MM月DD日论文/
   ├─ review/
   ├─ deep_dive/
   └─ application/
```

## 首次配置顺序

以下命令均在 `D:\每日论文阅读\embodied_ai_paper_system` 中执行。

### 1. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 填写私密配置

复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

打开 `.env` 并填写：

```dotenv
DEEPSEEK_API_KEY=你的密钥
SEMANTIC_SCHOLAR_API_KEY=你的可选密钥
OBSIDIAN_VAULT_PATH=D:\你的\Obsidian库
```

`SEMANTIC_SCHOLAR_API_KEY` 可留空，但无 Key 时限流更严格。不要把 `.env`
提交到 Git 或发给他人。

若日志出现 `HTTP 429`，表示 Semantic Scholar 正在限流。程序会读取服务端的
`Retry-After` 并自动等待，单个关键词失败也不会中断整批任务。无 Key 用户仍可能
需要隔一段时间重新运行；长期自动运行建议申请 API Key。

### 3. 调整关键词

编辑 `config/keywords.yaml`。默认关键词已填好，可直接使用。

### 4. 首次更新基石论文库

```powershell
python main.py landmarks --force
```

结果写入本地运行文件 `config/landmark_papers.json`。该文件不会上传 GitHub；
可版本控制的空模板为 `config/landmark_papers.example.json`。之后每天运行时只有文件超过 7 天才会
再次更新；也可由每周计划任务独立更新。

### 5. 手动完成一次全流程测试

```powershell
python main.py daily
```

检查：

- `logs/当天日期.log` 没有未处理错误；
- Obsidian 中出现当日日报；
- 日报内 PDF 链接可以直接打开；
- `data/history/recommendations.json` 已记录三篇论文。

`data/history/recommendations.json` 是本地运行状态，不会上传 GitHub。

重复测试可使用 `python main.py daily --force`，但会覆盖同名日报和复用已下载 PDF。

## 设置 Windows 自动运行

推荐使用“任务计划程序”，不要让 Python 进程常驻 24 小时。

### 每日任务

- 触发器：每天 `07:00`。
- 程序：`powershell.exe`
- 参数：

```text
-NoProfile -ExecutionPolicy Bypass -File "D:\每日论文阅读\embodied_ai_paper_system\scripts\run_daily.ps1"
```

### 每周基石任务

- 触发器：每周日 `02:00`。
- 程序：`powershell.exe`
- 参数：

```text
-NoProfile -ExecutionPolicy Bypass -File "D:\每日论文阅读\embodied_ai_paper_system\scripts\run_weekly_landmarks.ps1"
```

两个任务都建议启用：

- 错过计划时间后尽快运行；
- 失败后每 30 分钟重试，最多 3 次；
- 允许唤醒计算机；
- 运行超过 2 小时则停止；
- 不启动新的并行实例。

任务成功时不会弹窗，只写日志；失败时会弹出提示，并显示当天日志文件路径。
日志目录为 `D:\每日论文阅读\embodied_ai_paper_system\logs\`，文件名格式为
`YYYY-MM-DD.log`。

电脑关机时无法执行，但开机后可以补跑。真正 24 小时在线需要将项目放到 NAS、
云主机或长期在线设备，并让该设备能访问同步后的 Obsidian Vault。

## 常用命令

```powershell
python main.py daily
python main.py daily --force
python main.py landmarks
python main.py landmarks --force
python -m unittest discover -s tests
```

## 当前需要用户填写的内容

只有 `.env` 中的以下内容必须由用户提供：

- `DEEPSEEK_API_KEY`
- `OBSIDIAN_VAULT_PATH`
- `SEMANTIC_SCHOLAR_API_KEY`（可选）

基石论文库初始为空，首次运行每周任务后自动生成，不需要手工填写。

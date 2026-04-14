# 合同智能审核系统

基于 AI 的合同智能审核 MVP 系统，支持 Word 和 PDF 文档的自动审核。

## 功能特性

- 支持 Word (.docx) 和 PDF 文档解析
- 基于 AI 的合同条款智能分析
- 可配置的业务规则引擎
- 审核意见自动生成
- RESTful API 接口

## 技术栈

- **框架**: FastAPI + Uvicorn
- **AI 集成**: 支持多模型配置
- **文档解析**: python-docx, PyMuPDF, markitdown
- **数据库**: SQLite (aiosqlite)
- **数据验证**: Pydantic v2

## 快速开始（Windows）

下面给出在 Windows（PowerShell / CMD）下的最小可执行步骤，以及 VS Code 调试说明。

### 先决条件

- 已安装 Python 3.8+（建议 3.10+ 或 3.12）
- 在项目根目录（本仓库根）运行下面命令

### 创建并激活虚拟环境

PowerShell:
```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
```

CMD:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 安装依赖

推荐使用项目中已有的 `contract_audit/requirements.txt`：

```powershell
pip install --upgrade pip
pip install -r contract_audit\requirements.txt
```

或者使用项目根新增的安装脚本（已包含在仓库）：

```powershell
.\scripts\setup_windows.ps1         # 创建 venv、升级 pip 并安装依赖
.\scripts\setup_windows.ps1 -RunApp # 同时启动应用（可选）
.\scripts\setup_windows.ps1 -RunTests # 安装并运行 pytest（可选）
```

### 运行应用（本地）

项目默认已将 Uvicorn 运行端口修改为 `9999`。推荐在 `contract_audit` 目录下以虚拟环境的 Python 启动：

```powershell
cd contract_audit
..\ .venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 9999
```

或者（已修改 `main.py` 默认端口）：

```powershell
cd contract_audit
python main.py
```

健康检查:

```
GET http://127.0.0.1:9999/health
```

API 文档（启动后）:
- Swagger UI: `http://127.0.0.1:9999/docs`
- ReDoc: `http://127.0.0.1:9999/redoc`

### 在 VS Code 中调试

- 已更新调试配置文件：`.vscode/launch.json`，添加了 "Python: FastAPI 调试" 配置，使用工作区虚拟环境的 Python 以模块方式启动 `uvicorn`，端口为 `9999`。
- 在 VS Code 中选择配置 `Python: FastAPI 调试`，按 F5 启动调试（会在 `contract_audit` 目录下以 `main:app` 运行，支持热重载）。

### 运行测试

如果需要运行测试：

```powershell
.venv\Scripts\Activate.ps1
pip install pytest
pytest -q
```

### 配置项与环境变量

- 数据库文件位于：`contract_audit/data/contract_audit.db`（使用 SQLite，首次运行时会自动创建）
- AI 提供商密钥等请在 `contract_audit/config.py` 中配置，或通过环境变量/你的部署方式注入。

### 常见问题

- 如果启动时报 `ModuleNotFoundError: No module named 'models'`，请确保以 `contract_audit` 为当前工作目录运行 uvicorn（launch.json 与上面的命令已做相应处理）。
- 若 PowerShell 无法激活脚本，可能受执行策略限制，临时解决：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---
如需我将 README 中的命令改为适配你的常用 shell（例如 Git Bash / WSL），或把启动脚本改为 cross-platform 版本，请告诉我。

## 项目结构

```
contract_audit/
├── main.py              # FastAPI 入口
├── config.py            # 配置管理
├── models/              # 数据模型
│   ├── schema.py        # Pydantic 模型
│   └── database.py      # 数据库操作
├── routers/             # API 路由
│   ├── audit.py         # 审核接口
│   ├── rule.py          # 规则管理
│   └── ai_config.py     # AI 配置
├── services/            # 业务逻辑
│   ├── parser.py        # 文档解析
│   ├── auditor.py        # 审核引擎
│   └── ai_client.py     # AI 客户端
└── tests/               # 测试文件
```

## License

MIT

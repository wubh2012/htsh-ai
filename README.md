# 内容审核系统

基于 AI 的内容审核系统，支持 Word (.docx) 和 PDF 文档的自动审核，可按业务规则分析文档内容并生成审核意见。

## 功能特性

- 支持 Word (.docx) 和 PDF 文档解析
- 基于 AI 的文档内容智能分析
- 可配置的业务规则引擎（14 条默认审核规则）
- 审核意见自动生成
- RESTful API + 前端界面

## 环境要求

- Python 3.10+
- Windows / macOS / Linux

## 本地运行步骤

### 1. 克隆项目

```bash
git clone https://github.com/wubh2012/htsh-ai
cd htsh-ai
```

### 2. 创建并激活虚拟环境

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r contract_audit/requirements.txt
```

### 4. 启动服务

```bash
cd contract_audit
python main.py
```

### 5. 配置 AI

首次使用需在页面配置 AI 提供商的 API Key：打开前端界面 → 进入「AI 配置」页面填写。

支持的 AI 提供商：SiliconFlow、智谱 AI (ZhipuAI)、阿里云 DashScope、OpenAI

## 启动项目

```powershell
cd contract_audit
python main.py
```

或者使用 uvicorn：

```powershell
cd contract_audit
python -m uvicorn main:app --reload --host 0.0.0.0 --port 9999
```

## 访问应用

启动后访问：

| 服务 | 地址 |
|------|------|
| 前端界面 | http://127.0.0.1:9999/ |
| API 文档 (Swagger) | http://127.0.0.1:9999/docs |
| API 文档 (ReDoc) | http://127.0.0.1:9999/redoc |
| 健康检查 | http://127.0.0.1:9999/health |

## 项目结构

```
contract_audit/
├── main.py              # FastAPI 入口
├── config.py            # 配置文件
├── requirements.txt     # 依赖列表
├── models/              # 数据模型
│   ├── schema.py        # Pydantic 模型
│   └── database.py      # 数据库操作
├── routers/             # API 路由
│   ├── audit.py         # 审核接口
│   ├── rule.py          # 规则管理
│   └── ai_config.py     # AI 配置
├── services/            # 业务逻辑
│   ├── parser.py        # 文档解析
│   ├── auditor.py       # 审核引擎
│   └── ai_client.py     # AI 客户端
├── static/              # 前端资源
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── data/                # 数据库 (自动创建)
│   └── contract_audit.db
└── uploads/              # 上传文件 (自动创建)
```

## 常见问题

**Q: 启动时报 `ModuleNotFoundError: No module named 'models'`**
A: 确保在 `contract_audit` 目录下运行，或使用 `cd contract_audit && python main.py`

**Q: PowerShell 无法激活虚拟环境**
A: 执行 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Q: 数据库在哪里？**
A: SQLite 数据库会在首次启动时自动创建于 `contract_audit/data/contract_audit.db`

**Q: 如何查看/修改审核规则？**
A: 通过前端界面的"规则管理"页面，或调用 `/api/rule` 相关接口

## License

MIT

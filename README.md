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
- **文档解析**: python-docx, PyMuPDF
- **数据库**: SQLite (aiosqlite)
- **数据验证**: Pydantic v2

## 快速开始

### 安装依赖

```bash
cd contract_audit
pip install -r requirements.txt
```

### 启动服务

```bash
cd contract_audit
python main.py
```

服务将在 `http://localhost:8000` 启动

### API 文档

启动后访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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

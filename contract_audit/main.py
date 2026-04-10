"""FastAPI入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from models.database import init_database
from routers import rule, audit, ai_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_database()
    yield
    # 关闭时清理（如果需要）


app = FastAPI(
    title="合同智能审核系统",
    description="基于AI的合同智能审核MVP系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(rule.router)
app.include_router(audit.router)
app.include_router(ai_config.router)


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "contract-audit"}


# 挂载静态文件（前端）
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

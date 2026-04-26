"""内容审核系统 FastAPI 入口。

职责边界：创建 Web 应用、注册 API 路由、挂载静态前端资源并提供健康检查。
关键副作用：应用启动时初始化本地 SQLite 数据库；运行期间读取静态文件并响应 HTTP 请求。
关键依赖与约束：依赖 models.database.init_database 完成数据库准备，依赖 routers 包提供业务 API。
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.database import init_database
from routers import rule, audit, ai_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理 FastAPI 应用生命周期。

    :param app: 当前 FastAPI 应用实例；由框架注入，不允许为空。
    :return: 异步上下文管理器，启动阶段完成初始化，关闭阶段当前不执行额外清理。
    :raises Exception: 当数据库初始化失败时向上抛出，阻止服务以不完整状态启动。
    :side effects: 创建或迁移本地 SQLite 数据库文件，并可能写入默认规则数据。
    """
    # 启动时初始化数据库
    await init_database()
    yield
    # 关闭时清理（如果需要）


app = FastAPI(
    title="内容审核系统",
    description="基于AI的内容审核MVP系统",
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

# 注册路由 - API路由必须在StaticFiles挂载之前
app.include_router(rule.router)
app.include_router(audit.router)
app.include_router(ai_config.router)

# 健康检查
@app.get("/health")
async def health_check():
    """返回服务健康状态。

    :return: 包含运行状态与服务标识的字典，用于人工检查、部署探活或监控探测。
    :raises Exception: 正常情况下不主动抛出异常；若 FastAPI 响应序列化失败则由框架处理。
    :side effects: 无外部 I/O，不读取或修改数据库、文件、网络状态。
    """
    return {"status": "healthy", "service": "content-audit"}

# 挂载静态文件（前端）
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# 使用 StaticFiles 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 根路径返回index.html
@app.get("/")
async def root():
    """返回前端单页应用入口。

    :return: static/index.html 文件响应，用于浏览器加载内容审核系统前端。
    :raises RuntimeError: 当静态文件路径不存在或不可读时由 FileResponse/底层文件读取抛出。
    :side effects: 读取本地 index.html 文件，不修改文件、数据库或全局状态。
    """
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(static_dir, "index.html"))

# SPA fallback - 必须在 StaticFiles 挂载之后
@app.get("/{path:path}")
async def spa_fallback(path: str):
    """为前端路由提供 SPA 回退响应。

    :param path: 浏览器请求路径；非 api/static 前缀会回退到 index.html，api/static 前缀返回 404。
    :return: 非 API/静态资源路径返回前端入口文件。
    :raises HTTPException: 当请求路径属于 API 或静态资源但未匹配到已注册路由时返回 404。
    :side effects: 只读取本地 index.html 文件，不写入外部资源或修改应用状态。
    """
    if not path.startswith("api") and not path.startswith("static"):
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(static_dir, "index.html"))
    raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9999, reload=True)

# ============ 第一阶段：构建 ============
FROM crpi-duv8qv3cuwuwgicp.cn-hangzhou.personal.cr.aliyuncs.com/aalmix-docker-2025/python:3.10-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libjpeg-dev \
    tcl \
    tk \
    && rm -rf /var/lib/apt/lists/*

# 复制所有代码（构建需要）
COPY contract_audit/ ./contract_audit/
COPY pyproject.toml .

# 安装 Python 依赖（--user 需要设置 PATH）
RUN pip install --no-cache-dir --user -e . && \
    find /root/.local -name "*.pyc" -delete && \
    find /root/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# ============ 第二阶段：运行 ============
FROM crpi-duv8qv3cuwuwgicp.cn-hangzhou.personal.cr.aliyuncs.com/aalmix-docker-2025/python:3.10-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    libjpeg-dev \
    tcl \
    tk \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制已安装的包
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/contract_audit /app/contract_audit
COPY pyproject.toml .

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 9999

# 启动命令
CMD ["uvicorn", "contract_audit.main:app", "--host", "0.0.0.0", "--port", "9999"]

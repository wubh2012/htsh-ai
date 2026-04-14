"""配置文件"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库路径
DATABASE_PATH = os.path.join(BASE_DIR, "data", "contract_audit.db")

# 上传文件存储路径
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# AI Provider 配置
AI_PROVIDERS = {
    "zhipuai": {
        "name": "智谱AI",
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4",
        "api_key": "",  # 需要用户配置
    },
    "dashscope": {
        "name": "通义千问",
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-turbo",
        "api_key": "",  # 需要用户配置
    },
    "openai": {
        "name": "OpenAI GPT",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "api_key": "",  # 需要用户配置
    },
    "siliconflow": {
        "name": "硅基流动",
        "endpoint": "https://api.siliconflow.cn/v1/chat/completions",
        "model": "deepseek-ai/DeepSeek-V3.2",
        "api_key": "sk-vcuwkdvtaiqskoxysaigkadbqoprprejgyncfkandqdlhtyv",  # 需要用户配置
    },
}

# 默认AI Provider
DEFAULT_PROVIDER = "siliconflow"

# 合同文本分段大小（字符数）
TEXT_CHUNK_SIZE = 80000

# 支持的文件类型
SUPPORTED_FILE_TYPES = ["docx", "pdf"]

# 最大文件大小（MB）
MAX_FILE_SIZE = 10

"""数据库连接与表初始化"""
import aiosqlite
import os
from contextlib import asynccontextmanager
from config import DATABASE_PATH

# 确保data目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 建表SQL
CREATE_TABLES_SQL = """
-- 规则表
CREATE TABLE IF NOT EXISTS audit_rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    check_content VARCHAR(500) NOT NULL,
    risk_level INTEGER DEFAULT 3,
    suggestion TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 审核结果表
CREATE TABLE IF NOT EXISTS audit_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    content_text TEXT,
    ai_conclusion VARCHAR(20),
    ai_result JSON,
    audit_status VARCHAR(20) DEFAULT 'PENDING',
    auditor_comment TEXT,
    auditor_id INTEGER,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    audit_time DATETIME
);

-- AI配置表
CREATE TABLE IF NOT EXISTS ai_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider VARCHAR(50) NOT NULL UNIQUE,
    api_key VARCHAR(200) NOT NULL,
    endpoint VARCHAR(500),
    model VARCHAR(100),
    enabled BOOLEAN DEFAULT FALSE,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

INIT_DEFAULT_RULES_SQL = """
INSERT OR IGNORE INTO audit_rule (id, rule_name, rule_type, check_content, risk_level, suggestion, enabled)
VALUES
    (1, '保密条款检查', 'CHECK_MISSING', '保密条款', 3, '建议在合同中添加保密条款，明确保密范围和保密期限', TRUE),
    (2, '违约金条款检查', 'CHECK_MISSING', '违约金', 4, '建议明确约定违约金金额或计算方式', TRUE),
    (3, '争议解决条款检查', 'CHECK_MISSING', '争议解决', 3, '建议添加争议解决条款，明确仲裁或诉讼管辖', TRUE),
    (4, '争议解决方式-诉讼管辖', 'RISK_KEYWORD', '向有管辖权的人民法院提起诉讼|提请仲裁委员会|申请仲裁解决', 4, '争议解决条款建议统一为：向甲方所在地人民法院提起诉讼', TRUE),
    (5, '法律依据有效性', 'RISK_KEYWORD', '合同法', 5, '《合同法》已失效，应改为《民法典》', TRUE),
    (6, '知识产权侵权责任', 'CHECK_MISSING', '知识产权', 4, '建议增加条款明确乙方应保证合同标的物不侵犯第三人知识产权', TRUE),
    (7, '质量标准明确性', 'CHECK_MISSING', '国家现行标准|行业标准', 3, '合同中涉及多个标准时需明确适用哪个标准，建议选用较高标准', TRUE),
    (8, '合同有效期明确', 'CHECK_MISSING', '合同有效期', 3, '建议明确合同有效期起止时间，建议表述为：自合同签订之日起至合同履行完毕之日止', TRUE),
    (9, '产品服务范围明确', 'CHECK_MISSING', '使用范围|使用期限|使用方式', 3, '涉及产品或服务使用时，建议明确使用范围、方法、期限、折扣等', TRUE),
    (10, '传真扫描件效力条款', 'RISK_KEYWORD', '传真签署|扫描件.*同等法律效力', 3, '建议删除合同中关于传真签署和扫描件与正本具有同等法律效力的约定', TRUE),
    (11, '保修责任明确', 'CHECK_MISSING', '保修|售后', 3, '建议明确保修责任和技术服务提供商的保修责任', TRUE),
    (12, '违约金与付款重复', 'RISK_KEYWORD', '违约金.*付款|付款.*违约金', 2, '违约责任条款与付款相关约定重复时，建议删除重复内容', TRUE),
    (13, '逾期竣工违约金上限', 'CHECK_MISSING', '逾期竣工违约金', 4, '逾期竣工违约金最高限额比例设置较低，建议适当调整或在违约责任部分增加解除合同条款', TRUE),
    (14, '争议解决友好协商', 'CHECK_MISSING', '友好协商', 2, '争议解决条款建议明确协商前置程序和协商期限（如协商不成可诉讼）', TRUE);
"""


INIT_DEFAULT_AI_CONFIG_SQL = """
INSERT OR IGNORE INTO ai_config (provider, api_key, endpoint, model, enabled)
VALUES ('DeepSeek', '', 'https://api.deepseek.com', 'deepseek-chat', FALSE);
"""

async def init_database():
    """初始化数据库，创建表和默认数据"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 执行建表SQL
        for statement in CREATE_TABLES_SQL.strip().split(';'):
            statement = statement.strip()
            if statement:
                await db.execute(statement)

        # 插入默认规则
        await db.executescript(INIT_DEFAULT_RULES_SQL)
        # 插入默认DeepSeek AI配置
        await db.executescript(INIT_DEFAULT_AI_CONFIG_SQL)
        await db.commit()


@asynccontextmanager
async def get_db():
    """获取数据库连接的上下文管理器"""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

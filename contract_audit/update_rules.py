"""更新规则数据"""
import asyncio
import aiosqlite
from config import DATABASE_PATH

NEW_RULES = [
    (4, '争议解决方式-诉讼管辖', 'RISK_KEYWORD', '向有管辖权的人民法院提起诉讼|提请仲裁委员会|申请仲裁解决', 4, '争议解决条款建议统一为：向甲方所在地人民法院提起诉讼', True),
    (5, '法律依据有效性', 'RISK_KEYWORD', '合同法', 5, '《合同法》已失效，应改为《民法典》', True),
    (6, '知识产权侵权责任', 'CHECK_MISSING', '知识产权', 4, '建议增加条款明确乙方应保证合同标的物不侵犯第三人知识产权', True),
    (7, '质量标准明确性', 'CHECK_MISSING', '国家现行标准|行业标准', 3, '合同中涉及多个标准时需明确适用哪个标准，建议选用较高标准', True),
    (8, '合同有效期明确', 'CHECK_MISSING', '合同有效期', 3, '建议明确合同有效期起止时间，建议表述为：自合同签订之日起至合同履行完毕之日止', True),
    (9, '产品服务范围明确', 'CHECK_MISSING', '使用范围|使用期限|使用方式', 3, '涉及产品或服务使用时，建议明确使用范围、方法、期限、折扣等', True),
    (10, '传真扫描件效力条款', 'RISK_KEYWORD', '传真签署|扫描件.*同等法律效力', 3, '建议删除合同中关于传真签署和扫描件与正本具有同等法律效力的约定', True),
    (11, '保修责任明确', 'CHECK_MISSING', '保修|售后', 3, '建议明确保修责任和技术服务提供商的保修责任', True),
    (12, '违约金与付款重复', 'RISK_KEYWORD', '违约金.*付款|付款.*违约金', 2, '违约责任条款与付款相关约定重复时，建议删除重复内容', True),
    (13, '逾期竣工违约金上限', 'CHECK_MISSING', '逾期竣工违约金', 4, '逾期竣工违约金最高限额比例设置较低，建议适当调整或在违约责任部分增加解除合同条款', True),
    (14, '争议解决友好协商', 'CHECK_MISSING', '友好协商', 2, '争议解决条款建议明确协商前置程序和协商期限（如协商不成可诉讼）', True),
]

async def update_rules():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for rule in NEW_RULES:
            rule_id, rule_name, rule_type, check_content, risk_level, suggestion, enabled = rule
            try:
                await db.execute("""
                    INSERT INTO audit_rule (id, rule_name, rule_type, check_content, risk_level, suggestion, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (rule_id, rule_name, rule_type, check_content, risk_level, suggestion, enabled))
                print(f"已添加规则: {rule_name}")
            except aiosqlite.IntegrityError:
                print(f"规则已存在，跳过: {rule_name}")
        await db.commit()
        print("规则更新完成")

if __name__ == "__main__":
    asyncio.run(update_rules())

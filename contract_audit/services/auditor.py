"""审核逻辑服务"""
import json
import re
from typing import List, Dict, Any, Optional
from models.database import get_db
from models.schema import RuleResponse, RiskPoint, AIResultDetail, AuditConclusion
from services.parser import DocumentParser
from services.ai_client import AIClient
from config import TEXT_CHUNK_SIZE


class Auditor:
    """审核逻辑服务"""

    def __init__(self, db):
        self.db = db
        self.parser = DocumentParser()

    async def get_enabled_rules(self) -> List[Dict[str, Any]]:
        """获取所有启用的规则"""
        cursor = await self.db.execute(
            "SELECT id, rule_name, rule_type, check_content, risk_level, suggestion "
            "FROM audit_rule WHERE enabled = TRUE"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def audit_contract(self, result_id: int, file_path: str, file_type: str,
                            provider: str = "zhipuai", api_key: Optional[str] = None) -> AIResultDetail:
        """
        审核合同
        :param result_id: 审核结果ID
        :param file_path: 合同文件路径
        :param file_type: 文件类型
        :param provider: AI Provider
        :param api_key: API密钥（可选）
        :return: 审核结果详情
        """
        # 1. 解析文档
        content_text = await self.parser.parse(file_path, file_type)

        # 更新审核结果的文本内容
        await self.db.execute(
            "UPDATE audit_result SET content_text = ? WHERE id = ?",
            (content_text, result_id)
        )
        await self.db.commit()

        # 2. 获取启用的规则
        rules = await self.get_enabled_rules()

        # 3. 构建Prompt
        prompt = self._build_audit_prompt(content_text, rules)

        # 4. 调用AI
        ai_client = AIClient(provider=provider, api_key=api_key)
        messages = [
            {"role": "system", "content": "你是一名专业的企业法务顾问，负责对合同文本进行初步法律合规性审查。你的任务是严格依据以下审核框架，逐条检查合同内容，识别潜在法律风险。\n\n【审核原则】\n. 仅基于合同原文作答，不得臆测或补充信息\n. 发现问题必须引用原文条款编号和具体内容\n. 每个问题需给出明确的修改建议\n. 无法确定的问题标注「需人工复核」"},
            {"role": "user", "content": prompt}
        ]

        ai_response = await ai_client.chat(messages)

        # 5. 解析AI响应
        result = self._parse_ai_response(ai_response, rules)

        # 6. 更新审核结果
        await self.db.execute(
            "UPDATE audit_result SET ai_conclusion = ?, ai_result = ? WHERE id = ?",
            (result.conclusion.value, result.model_dump_json(), result_id)
        )
        await self.db.commit()

        return result

    def _build_audit_prompt(self, content_text: str, rules: List[Dict[str, Any]]) -> str:
        """构建审核Prompt"""
        # 如果文本过长，分段处理
        if len(content_text) > TEXT_CHUNK_SIZE:
            content_text = content_text[:TEXT_CHUNK_SIZE] + "\n\n[...合同内容过长，已截断...]"

        if not rules:
            # 无规则时，进行通用法务审核
            prompt = f"""请作为专业法务顾问，对以下合同进行全面的法律合规性主动审查，涵盖以下方面：

1. 合同主体资格：双方是否具备相应民事行为能力，主体信息是否完整准确
2. 权利义务对等性：双方权利义务是否显著不对等，是否存在明显不公平条款
3. 必备条款完整性：标的、质量、价款、履行期限地点方式、违约责任等必备条款是否齐全
4. 常见法律风险：保密条款、知识产权归属、竞业限制、争议解决、不可抗力、格式条款等是否合理
5. 法律适用准确性：引用的法律法规是否现行有效（如《合同法》已废止需改《民法典》）
6. 合同表达清晰性：条款表述是否存在歧义、逻辑矛盾或理解分歧

【合同内容】
{content_text}

【输出要求】
请以JSON格式返回审核结果，包含以下字段：
- conclusion: 审核结论，"PASS"表示通过，"FAIL"表示不通过需要修改，"REVIEW"表示需要人工复核
- risk_points: 风险点列表，每个风险点包含：rule_id(填0), rule_name(风险类型名称), description(风险描述), suggestion(修改建议), risk_level(风险等级1-5)
- summary: 总体评价

请确保返回有效的JSON格式，不要包含其他文字。"""
            return prompt

        # 格式化规则
        rules_text = []
        for rule in rules:
            risk_level_str = "高" if rule["risk_level"] >= 4 else ("中" if rule["risk_level"] >= 3 else "低")
            rules_text.append(
                f"- 规则{rule['id']}: {rule['rule_name']} ({rule['rule_type']})\n"
                f"  检查内容: {rule['check_content']}\n"
                f"  风险等级: {risk_level_str} (1-5分)\n"
                f"  修改建议: {rule['suggestion'] or '无'}"
            )

        prompt = f"""请对以下合同进行全面的法律合规性审查，分为【规则审查】和【主动审查】两部分。

【规则审查】
请严格按照以下规则逐条检查合同是否触发风险：

{chr(10).join(rules_text)}

【主动审查】
在规则之外，作为专业法务顾问主动审查合同，涵盖以下方面：
1. 合同主体资格：双方是否具备相应民事行为能力，主体信息是否完整准确
2. 权利义务对等性：双方权利义务是否显著不对等，是否存在明显不公平条款
3. 必备条款完整性：标的、质量、价款、履行期限地点方式、违约责任等必备条款是否齐全
4. 常见法律风险：保密条款、知识产权归属、竞业限制、争议解决、不可抗力、格式条款等是否合理
5. 法律适用准确性：引用的法律法规是否现行有效（如《合同法》已废止需改《民法典》）
6. 合同表达清晰性：条款表述是否存在歧义、逻辑矛盾或理解分歧

【合同内容】
{content_text}

【输出要求】
请以JSON格式返回审核结果，包含以下字段：
- conclusion: 审核结论，"PASS"表示通过，"FAIL"表示不通过需要修改，"REVIEW"表示需要人工复核
- risk_points: 风险点列表，每个风险点包含：rule_id(规则ID，规则外主动发现的风险填0), rule_name(规则名称或风险类型), description(风险描述), suggestion(修改建议), risk_level(风险等级1-5)
- summary: 总体评价

请确保返回有效的JSON格式，不要包含其他文字。"""

        return prompt

    def _parse_ai_response(self, ai_response: str, rules: List[Dict[str, Any]]) -> AIResultDetail:
        """解析AI响应"""
        # 尝试提取JSON部分
        json_text = self._extract_json(ai_response)

        try:
            data = json.loads(json_text)

            # 构建风险点
            risk_points = []
            for rp in data.get("risk_points", []):
                # 尝试解析rule_id，可能返回 "规则1" 或 "1" 或 1
                rule_id_val = rp.get("rule_id")
                rule_id = self._extract_rule_id(rule_id_val, rules)

                # 查找匹配的规则
                rule = next((r for r in rules if r["id"] == rule_id), None)
                if not rule and rule_id_val:
                    # 尝试按规则名称匹配
                    rule = next((r for r in rules if r["rule_name"] == str(rule_id_val)), None)

                # 解析风险等级
                risk_level = self._extract_risk_level(rp.get("risk_level"))

                risk_points.append(RiskPoint(
                    rule_id=rule_id,
                    rule_name=rp.get("rule_name") or (rule["rule_name"] if rule else "未知规则"),
                    description=rp.get("description", ""),
                    suggestion=rp.get("suggestion"),
                    risk_level=risk_level
                ))

            # 确定结论
            conclusion_str = data.get("conclusion", "REVIEW").upper()
            if conclusion_str not in ["PASS", "FAIL", "REVIEW"]:
                conclusion_str = "REVIEW"

            return AIResultDetail(
                conclusion=AuditConclusion(conclusion_str),
                risk_points=risk_points,
                summary=data.get("summary", "")
            )

        except json.JSONDecodeError as e:
            # JSON解析失败，返回需要人工复核
            return AIResultDetail(
                conclusion=AuditConclusion.REVIEW,
                risk_points=[],
                summary=f"AI返回格式解析失败，请人工复核。原始返回: {ai_response[:500]}"
            )

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON部分"""
        # 尝试提取markdown代码块
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        if matches:
            return matches[0].strip()

        # 尝试直接解析
        text = text.strip()

        # 如果文本以 [ 或 { 开头，直接返回
        if text.startswith("[") or text.startswith("{"):
            return text

        # 尝试找到JSON部分
        json_start = text.find("{")
        json_end = text.rfind("}")

        if json_start != -1 and json_end != -1 and json_start < json_end:
            return text[json_start:json_end + 1]

        # 尝试找数组
        array_start = text.find("[")
        array_end = text.rfind("]")

        if array_start != -1 and array_end != -1 and array_start < array_end:
            return text[array_start:array_end + 1]

        # 无法提取，返回原始文本
        return text

    def _extract_rule_id(self, value, rules: List[Dict[str, Any]]) -> int:
        """从各种格式中提取规则ID"""
        if value is None:
            return 0

        # 如果是整数，直接返回
        if isinstance(value, int):
            return value

        # 如果是字符串，尝试提取数字
        value_str = str(value)

        # 尝试从 "规则1" 这种格式中提取数字
        import re
        match = re.search(r'\d+', value_str)
        if match:
            return int(match.group())

        # 尝试按规则名称匹配
        for rule in rules:
            if rule["rule_name"] == value_str:
                return rule["id"]

        return 0

    def _extract_risk_level(self, value) -> int:
        """从各种格式中提取风险等级"""
        if value is None:
            return 3

        # 如果是整数，直接返回
        if isinstance(value, int):
            return max(1, min(5, value))  # 限制在1-5范围

        # 如果是字符串
        value_str = str(value)

        # 如果是中文风险等级
        risk_map = {"很高": 5, "高": 4, "中": 3, "低": 2, "很低": 1}
        if value_str in risk_map:
            return risk_map[value_str]

        # 尝试提取数字
        import re
        match = re.search(r'\d+', value_str)
        if match:
            return max(1, min(5, int(match.group())))

        return 3

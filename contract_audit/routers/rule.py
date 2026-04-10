"""规则配置API"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.database import get_db
from models.schema import (
    RuleCreate, RuleUpdate, RuleResponse, MessageResponse
)

router = APIRouter(prefix="/api/rules", tags=["规则配置"])


@router.get("", response_model=List[RuleResponse])
async def get_rules():
    """获取所有规则"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, rule_name, rule_type, check_content, risk_level, suggestion, enabled, create_time, update_time "
            "FROM audit_rule ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: int):
    """获取单个规则"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, rule_name, rule_type, check_content, risk_level, suggestion, enabled, create_time, update_time "
            "FROM audit_rule WHERE id = ?", (rule_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"规则 {rule_id} 不存在")
        return dict(row)


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule: RuleCreate):
    """创建规则"""
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO audit_rule (rule_name, rule_type, check_content, risk_level, suggestion, enabled)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (rule.rule_name, rule.rule_type.value, rule.check_content, rule.risk_level, rule.suggestion, rule.enabled)
        )
        await db.commit()
        rule_id = cursor.lastrowid

        # 返回创建的规则
        cursor = await db.execute("SELECT * FROM audit_rule WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
        return dict(row)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: int, rule: RuleUpdate):
    """更新规则"""
    async with get_db() as db:
        # 检查规则是否存在
        cursor = await db.execute("SELECT id FROM audit_rule WHERE id = ?", (rule_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"规则 {rule_id} 不存在")

        # 构建更新语句
        update_fields = []
        update_values = []

        if rule.rule_name is not None:
            update_fields.append("rule_name = ?")
            update_values.append(rule.rule_name)
        if rule.rule_type is not None:
            update_fields.append("rule_type = ?")
            update_values.append(rule.rule_type.value)
        if rule.check_content is not None:
            update_fields.append("check_content = ?")
            update_values.append(rule.check_content)
        if rule.risk_level is not None:
            update_fields.append("risk_level = ?")
            update_values.append(rule.risk_level)
        if rule.suggestion is not None:
            update_fields.append("suggestion = ?")
            update_values.append(rule.suggestion)
        if rule.enabled is not None:
            update_fields.append("enabled = ?")
            update_values.append(rule.enabled)

        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        update_fields.append("update_time = CURRENT_TIMESTAMP")
        update_values.append(rule_id)

        await db.execute(
            f"UPDATE audit_rule SET {', '.join(update_fields)} WHERE id = ?",
            update_values
        )
        await db.commit()

        # 返回更新后的规则
        cursor = await db.execute("SELECT * FROM audit_rule WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
        return dict(row)


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_rule(rule_id: int):
    """删除规则"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM audit_rule WHERE id = ?", (rule_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"规则 {rule_id} 不存在")

        await db.execute("DELETE FROM audit_rule WHERE id = ?", (rule_id,))
        await db.commit()

        return MessageResponse(message=f"规则 {rule_id} 已删除")


@router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(rule_id: int):
    """启用/禁用规则"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, enabled FROM audit_rule WHERE id = ?", (rule_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"规则 {rule_id} 不存在")

        new_enabled = not bool(row["enabled"])
        await db.execute(
            "UPDATE audit_rule SET enabled = ?, update_time = CURRENT_TIMESTAMP WHERE id = ?",
            (new_enabled, rule_id)
        )
        await db.commit()

        # 返回更新后的规则
        cursor = await db.execute("SELECT * FROM audit_rule WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
        return dict(row)

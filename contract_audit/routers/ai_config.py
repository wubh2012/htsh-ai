"""AI配置 API"""
from typing import List

from fastapi import APIRouter, HTTPException, status

from models.database import get_db
from models.schema import (
    AIConfigCreate,
    AIConfigResponse,
    AIConfigUpdate,
    MessageResponse,
)

router = APIRouter(prefix="/api/ai-config", tags=["AI配置"])


@router.get("", response_model=List[AIConfigResponse])
async def get_ai_configs():
    """获取所有 AI 配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, provider, api_key, endpoint, model, enabled, create_time "
            "FROM ai_config ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/{provider}", response_model=AIConfigResponse)
async def get_ai_config(provider: str):
    """获取指定名称的 AI 配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, provider, api_key, endpoint, model, enabled, create_time "
            "FROM ai_config WHERE provider = ?",
            (provider,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"AI配置 {provider} 不存在")
        return dict(row)


@router.post("", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(config: AIConfigCreate):
    """创建 AI 配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM ai_config WHERE provider = ?",
            (config.provider,),
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"AI配置 {config.provider} 已存在，请使用PUT更新",
            )

        cursor = await db.execute(
            """
            INSERT INTO ai_config (provider, api_key, endpoint, model, enabled)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                config.provider,
                config.api_key,
                config.endpoint,
                config.model,
                config.enabled,
            ),
        )
        await db.commit()
        config_id = cursor.lastrowid

        if config.enabled:
            await db.execute(
                "UPDATE ai_config SET enabled = FALSE WHERE id != ? AND provider != ?",
                (config_id, config.provider),
            )
            await db.commit()

        cursor = await db.execute("SELECT * FROM ai_config WHERE id = ?", (config_id,))
        row = await cursor.fetchone()
        return dict(row)


@router.put("/{provider}", response_model=AIConfigResponse)
async def update_ai_config(provider: str, config: AIConfigUpdate):
    """更新 AI 配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM ai_config WHERE provider = ?",
            (provider,),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"AI配置 {provider} 不存在")

        payload = config.model_dump(exclude_unset=True)
        new_provider = payload.get("provider", provider)

        if "provider" in payload and new_provider != provider:
            cursor = await db.execute(
                "SELECT id FROM ai_config WHERE provider = ?",
                (new_provider,),
            )
            if await cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail=f"AI配置 {new_provider} 已存在，请使用其他名称",
                )

        field_mapping = {
            "provider": "provider",
            "api_key": "api_key",
            "endpoint": "endpoint",
            "model": "model",
            "enabled": "enabled",
        }

        update_fields = []
        update_values = []
        for field_name, db_field in field_mapping.items():
            if field_name in payload:
                update_fields.append(f"{db_field} = ?")
                update_values.append(payload[field_name])

        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        update_values.append(provider)
        await db.execute(
            f"UPDATE ai_config SET {', '.join(update_fields)} WHERE provider = ?",
            update_values,
        )

        if payload.get("enabled") is True:
            await db.execute(
                "UPDATE ai_config SET enabled = FALSE WHERE provider != ?",
                (new_provider,),
            )

        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM ai_config WHERE provider = ?",
            (new_provider,),
        )
        row = await cursor.fetchone()
        return dict(row)


@router.delete("/{provider}", response_model=MessageResponse)
async def delete_ai_config(provider: str):
    """删除 AI 配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM ai_config WHERE provider = ?",
            (provider,),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"AI配置 {provider} 不存在")

        await db.execute("DELETE FROM ai_config WHERE provider = ?", (provider,))
        await db.commit()

        return MessageResponse(message=f"AI配置 {provider} 已删除")

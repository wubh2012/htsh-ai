"""AI配置API"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.database import get_db
from models.schema import (
    AIConfigCreate, AIConfigUpdate, AIConfigResponse, MessageResponse
)
from services.ai_client import AIClient

router = APIRouter(prefix="/api/ai-config", tags=["AI配置"])


@router.get("", response_model=List[AIConfigResponse])
async def get_ai_configs():
    """获取所有AI配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, provider, api_key, endpoint, model, enabled, create_time "
            "FROM ai_config ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/providers")
async def get_providers():
    """获取支持的AI Provider列表"""
    providers = []
    for key in AIClient.get_supported_providers():
        info = AIClient.get_provider_info(key)
        providers.append({
            "key": key,
            "name": info.get("name", key),
            "model": info.get("model", "")
        })
    return {"providers": providers}


@router.get("/{provider}", response_model=AIConfigResponse)
async def get_ai_config(provider: str):
    """获取指定Provider的配置"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, provider, api_key, endpoint, model, enabled, create_time "
            "FROM ai_config WHERE provider = ?", (provider,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"AI配置 {provider} 不存在")
        return dict(row)


@router.post("", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(config: AIConfigCreate):
    """创建AI配置"""
    async with get_db() as db:
        # 检查provider是否已存在
        cursor = await db.execute(
            "SELECT id FROM ai_config WHERE provider = ?", (config.provider,)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"AI配置 {config.provider} 已存在，请使用PUT更新"
            )

        cursor = await db.execute(
            """INSERT INTO ai_config (provider, api_key, endpoint, model, enabled)
               VALUES (?, ?, ?, ?, ?)""",
            (config.provider, config.api_key, config.endpoint, config.model, config.enabled)
        )
        await db.commit()
        config_id = cursor.lastrowid

        # 如果启用该配置，自动禁用其他配置
        if config.enabled:
            await db.execute(
                "UPDATE ai_config SET enabled = FALSE WHERE id != ? AND provider != ?",
                (config_id, config.provider)
            )
            await db.commit()

        # 返回创建的配置
        cursor = await db.execute("SELECT * FROM ai_config WHERE id = ?", (config_id,))
        row = await cursor.fetchone()
        return dict(row)


@router.put("/{provider}", response_model=AIConfigResponse)
async def update_ai_config(provider: str, config: AIConfigUpdate):
    """更新AI配置"""
    async with get_db() as db:
        # 检查配置是否存在
        cursor = await db.execute("SELECT id FROM ai_config WHERE provider = ?", (provider,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"AI配置 {provider} 不存在")

        # 构建更新语句
        update_fields = []
        update_values = []

        if config.api_key is not None:
            update_fields.append("api_key = ?")
            update_values.append(config.api_key)
        if config.endpoint is not None:
            update_fields.append("endpoint = ?")
            update_values.append(config.endpoint)
        if config.model is not None:
            update_fields.append("model = ?")
            update_values.append(config.model)
        if config.enabled is not None:
            update_fields.append("enabled = ?")
            update_values.append(config.enabled)

        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        update_values.append(provider)

        await db.execute(
            f"UPDATE ai_config SET {', '.join(update_fields)} WHERE provider = ?",
            update_values
        )

        # 如果启用该配置，自动禁用其他配置
        if config.enabled:
            await db.execute(
                "UPDATE ai_config SET enabled = FALSE WHERE provider != ?",
                (provider,)
            )

        await db.commit()

        # 返回更新后的配置
        cursor = await db.execute("SELECT * FROM ai_config WHERE provider = ?", (provider,))
        row = await cursor.fetchone()
        return dict(row)


@router.delete("/{provider}", response_model=MessageResponse)
async def delete_ai_config(provider: str):
    """删除AI配置"""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM ai_config WHERE provider = ?", (provider,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"AI配置 {provider} 不存在")

        await db.execute("DELETE FROM ai_config WHERE provider = ?", (provider,))
        await db.commit()

        return MessageResponse(message=f"AI配置 {provider} 已删除")

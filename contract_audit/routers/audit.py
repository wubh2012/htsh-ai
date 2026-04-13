"""审核流程API"""
import os
import uuid
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import List
from models.database import get_db
from models.schema import (
    UploadResponse, AuditResponse, AuditListItem, ReviewRequest,
    AuditStatus, MessageResponse, AIResultDetail
)
from services.parser import DocumentParser
from services.auditor import Auditor
from config import UPLOAD_DIR, MAX_FILE_SIZE

router = APIRouter(prefix="/api", tags=["审核流程"])

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_contract(file: UploadFile = File(...)):
    """
    上传合同文档
    - 支持 .docx 和 .pdf 格式
    - 最大文件大小: 10MB
    """
    # 验证文件类型
    file_type = DocumentParser.validate_file_type(file.filename)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式，仅支持 .docx 和 .pdf"
        )

    # 检查文件大小
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to start

    if size > MAX_FILE_SIZE * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制，最大 {MAX_FILE_SIZE}MB"
        )

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 存入数据库
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO audit_result (contract_name, file_path, file_type, audit_status)
               VALUES (?, ?, ?, 'PENDING')""",
            (file.filename, file_path, file_type)
        )
        await db.commit()
        result_id = cursor.lastrowid

    return UploadResponse(
        result_id=result_id,
        contract_name=file.filename,
        message="上传成功"
    )


@router.get("/audit/list", response_model=List[AuditListItem])
async def get_audit_list(limit: int = 50, offset: int = 0):
    """获取审核列表"""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, contract_name, file_type, ai_conclusion, audit_status, create_time
               FROM audit_result
               ORDER BY create_time DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.post("/audit/{result_id}")
async def start_audit(result_id: int):
    """
    发起AI审核
    - 解析合同文档
    - 调用AI进行审核
    - 返回审核结果
    """
    async with get_db() as db:
        # 检查审核结果是否存在
        cursor = await db.execute(
            "SELECT id, contract_name, file_path, file_type FROM audit_result WHERE id = ?",
            (result_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"审核记录 {result_id} 不存在")

        # 获取启用的AI配置
        cursor = await db.execute(
            "SELECT provider, api_key FROM ai_config WHERE enabled = TRUE LIMIT 1"
        )
        ai_config = await cursor.fetchone()

        if not ai_config:
            raise HTTPException(
                status_code=400,
                detail="未启用任何AI配置，请先在AI配置中启用一个Provider"
            )

        # 执行审核
        auditor = Auditor(db)
        try:
            result = await auditor.audit_contract(
                result_id=result_id,
                file_path=row["file_path"],
                file_type=row["file_type"],
                provider=ai_config["provider"],
                api_key=ai_config["api_key"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")

        # 重新获取更新后的数据
        cursor = await db.execute(
            "SELECT * FROM audit_result WHERE id = ?", (result_id,)
        )
        row = await cursor.fetchone()

        return {
            "result_id": result_id,
            "contract_name": row["contract_name"],
            "ai_conclusion": row["ai_conclusion"],
            "ai_result": result.model_dump() if result else None,
            "audit_status": row["audit_status"],
            "auditor_comment": row["auditor_comment"],
            "create_time": row["create_time"]
        }


@router.get("/audit/{result_id}", response_model=AuditResponse)
async def get_audit_result(result_id: int):
    """获取审核结果"""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, contract_name, file_type, ai_conclusion, ai_result,
                      audit_status, auditor_comment, create_time
               FROM audit_result WHERE id = ?""",
            (result_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"审核记录 {result_id} 不存在")

        result = {
            "result_id": row["id"],
            "contract_name": row["contract_name"],
            "ai_conclusion": row["ai_conclusion"],
            "audit_status": row["audit_status"],
            "auditor_comment": row["auditor_comment"],
            "create_time": row["create_time"]
        }

        # 解析AI结果JSON
        if row["ai_result"]:
            try:
                import json
                result["ai_result"] = json.loads(row["ai_result"])
            except:
                result["ai_result"] = None
        else:
            result["ai_result"] = None

        return result


@router.post("/audit/{result_id}/approve", response_model=MessageResponse)
async def approve_audit(result_id: int, request: ReviewRequest = ReviewRequest()):
    """人工通过审核"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, audit_status FROM audit_result WHERE id = ?", (result_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"审核记录 {result_id} 不存在")

        if row["audit_status"] == "APPROVED":
            raise HTTPException(status_code=400, detail="该审核已通过，无需重复操作")

        await db.execute(
            """UPDATE audit_result
               SET audit_status = 'APPROVED', auditor_comment = ?,
                   auditor_id = ?, audit_time = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (request.auditor_comment, request.auditor_id, result_id)
        )
        await db.commit()

        return MessageResponse(message="审核已通过")


@router.delete("/audit/{result_id}", response_model=MessageResponse)
async def delete_audit(result_id: int):
    """删除审核记录"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, file_path FROM audit_result WHERE id = ?", (result_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"审核记录 {result_id} 不存在")

        # 删除文件
        if row["file_path"] and os.path.exists(row["file_path"]):
            try:
                os.remove(row["file_path"])
            except Exception:
                pass  # 文件删除失败不影响记录删除

        # 删除数据库记录
        await db.execute("DELETE FROM audit_result WHERE id = ?", (result_id,))
        await db.commit()

        return MessageResponse(message="删除成功")


@router.post("/audit/{result_id}/reject", response_model=MessageResponse)
async def reject_audit(result_id: int, request: ReviewRequest = ReviewRequest()):
    """人工驳回审核"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, audit_status FROM audit_result WHERE id = ?", (result_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"审核记录 {result_id} 不存在")

        if row["audit_status"] == "REJECTED":
            raise HTTPException(status_code=400, detail="该审核已驳回，无需重复操作")

        await db.execute(
            """UPDATE audit_result
               SET audit_status = 'REJECTED', auditor_comment = ?,
                   auditor_id = ?, audit_time = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (request.auditor_comment, request.auditor_id, result_id)
        )
        await db.commit()

        return MessageResponse(message="审核已驳回")

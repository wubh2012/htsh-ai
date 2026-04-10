"""Pydantic模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RuleType(str, Enum):
    CHECK_MISSING = "CHECK_MISSING"
    RISK_KEYWORD = "RISK_KEYWORD"


class AuditConclusion(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class AuditStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ===== 规则相关模型 =====

class RuleBase(BaseModel):
    rule_name: str = Field(..., max_length=100, description="规则名称")
    rule_type: RuleType = Field(..., description="规则类型")
    check_content: str = Field(..., max_length=500, description="检查的条款名称或关键词")
    risk_level: int = Field(default=3, ge=1, le=5, description="风险等级 1-5")
    suggestion: Optional[str] = Field(None, description="修改建议")
    enabled: bool = Field(default=True, description="是否启用")


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=100)
    rule_type: Optional[RuleType] = None
    check_content: Optional[str] = Field(None, max_length=500)
    risk_level: Optional[int] = Field(None, ge=1, le=5)
    suggestion: Optional[str] = None
    enabled: Optional[bool] = None


class RuleResponse(RuleBase):
    id: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== AI配置相关模型 =====

class AIConfigBase(BaseModel):
    provider: str = Field(..., max_length=50, description="AI提供商")
    api_key: str = Field(..., max_length=200, description="API密钥")
    endpoint: Optional[str] = Field(None, max_length=500, description="API endpoint")
    model: Optional[str] = Field(None, max_length=100, description="模型名称")
    enabled: bool = Field(default=False, description="是否启用")


class AIConfigCreate(AIConfigBase):
    pass


class AIConfigUpdate(BaseModel):
    api_key: Optional[str] = Field(None, max_length=200)
    endpoint: Optional[str] = Field(None, max_length=500)
    model: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None


class AIConfigResponse(AIConfigBase):
    id: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== 审核结果相关模型 =====

class RiskPoint(BaseModel):
    rule_id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    description: str = Field(..., description="风险描述")
    suggestion: Optional[str] = Field(None, description="修改建议")
    risk_level: int = Field(..., description="风险等级")


class AIResultDetail(BaseModel):
    conclusion: AuditConclusion = Field(..., description="AI审核结论")
    risk_points: List[RiskPoint] = Field(default_factory=list, description="风险点列表")
    summary: str = Field(..., description="总体评价")


class UploadResponse(BaseModel):
    result_id: int = Field(..., description="审核结果ID")
    contract_name: str = Field(..., description="合同文件名")
    message: str = Field(default="上传成功")


class AuditResponse(BaseModel):
    result_id: int = Field(..., description="审核结果ID")
    contract_name: str = Field(..., description="合同文件名")
    ai_conclusion: Optional[AuditConclusion] = Field(None, description="AI结论")
    ai_result: Optional[AIResultDetail] = Field(None, description="AI详细结果")
    audit_status: AuditStatus = Field(..., description="审核状态")
    auditor_comment: Optional[str] = Field(None, description="复核意见")
    create_time: Optional[datetime] = Field(None, description="创建时间")


class AuditListItem(BaseModel):
    id: int
    contract_name: str
    file_type: str
    ai_conclusion: Optional[str] = None
    audit_status: AuditStatus
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    auditor_comment: Optional[str] = Field(None, description="复核意见")
    auditor_id: Optional[int] = Field(None, description="复核人ID")


# ===== 通用响应模型 =====

class MessageResponse(BaseModel):
    message: str
    success: bool = True

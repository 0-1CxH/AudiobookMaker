from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class StandardResponse(BaseModel):
    """标准API响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    error_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ProjectInfo(BaseModel):
    """项目信息"""
    project_id: str
    name: str
    exists: bool
    character_count: int = 0
    segment_count: int = 0
    allocated_dialogues: int = 0
    generated_audio_count: int = 0
    raw_text_length: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CharacterInfo(BaseModel):
    """角色信息"""
    name: str
    description: str
    requires_tts: bool = False
    voice_name: str = ""


class TextSegment(BaseModel):
    """文本片段"""
    index: int
    content: str
    tag: str
    allocated_speaker: Optional[str] = None
    has_audio: bool = False


class VoiceDesignInfo(BaseModel):
    """语音设计信息"""
    name: str
    tts_instruction: str
    reference_text: str = ""
    has_reference_audio: bool = False


class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    name: str
    raw_text: Optional[str] = ""
    settings: Optional[Dict[str, Any]] = None


class UpdateCharacterRequest(BaseModel):
    """更新角色请求"""
    description: Optional[str] = None
    requires_tts: Optional[bool] = None
    voice_name: Optional[str] = None


class AddCharacterRequest(BaseModel):
    """添加角色请求"""
    name: str
    description: Optional[str] = ""
    requires_tts: Optional[bool] = False
    voice_name: Optional[str] = ""


class UpdateDialogueRequest(BaseModel):
    """更新对话分配请求"""
    speaker: str


class GenerateCharacterDescriptionRequest(BaseModel):
    """生成角色描述请求"""
    suggestion: Optional[str] = ""
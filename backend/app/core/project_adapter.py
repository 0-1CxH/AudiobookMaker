import os
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import asdict
import sys

# 导入现有项目代码
from src.workflow import Project, ProjectSetting
from src.character import Character
from src.text import TaggedTextSegment
from src.voice import VoiceDesign


class ProjectAdapter:
    """项目适配器，包装现有Project类提供Web友好接口"""

    def __init__(self, project_id: str, config=None):
        """
        初始化项目适配器

        Args:
            project_id: 项目ID（项目名称）
            config: 配置对象，包含WORKSPACE_PATH等
        """
        self.project_id = project_id
        self.config = config
        self.project = None

        # 项目路径
        workspace_path = config.WORKSPACE_PATH if config else os.environ.get('WORKSPACE_PATH', './workspace')
        self.project_path = os.path.join(workspace_path, 'projects', project_id)

        # 加载或创建项目
        self._load_or_create_project()

    def _load_or_create_project(self):
        """加载或创建项目"""
        metadata_path = os.path.join(self.project_path, 'project_metadata.json')

        if os.path.exists(metadata_path):
            # 加载现有项目
            try:
                self.project = Project.load(self.project_id)
                print(f"Loaded existing project: {self.project_id}")
            except Exception as e:
                print(f"Failed to load project {self.project_id}: {e}")
                raise
        else:
            # 项目不存在，将在需要时创建
            self.project = None
    
    def save_project(self):
        """保存项目状态"""
        if self.project:
            try:
                self.project.save()
                print(f"Project {self.project_id} saved successfully")
            except Exception as e:
                print(f"Failed to save project {self.project_id}: {e}")
                raise

    def create_project(self, raw_text: str = "", settings: Optional[Dict] = None) -> Dict[str, Any]:
        """创建新项目"""
        try:
            # 创建项目设置
            project_settings = None
            if settings:
                project_settings = ProjectSetting(**settings)

            # 创建项目
            self.project = Project(
                name=self.project_id,
                raw_text=raw_text,
                project_setting=project_settings
            )

            # 保存项目
            self.project.save()

            return {
                'success': True,
                'project_id': self.project_id,
                'message': 'Project created successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        if not self.project:
            return {
                'exists': False,
                'project_id': self.project_id
            }

        return {
            'exists': True,
            'project_id': self.project_id,
            'name': self.project.name,
            'character_count': len(self.project.character_manager.characters),
            'segment_count': len(self.project.text_manager.data),
            'allocated_dialogues': len(self.project.text_manager.allocation_map),
            'generated_audio_count': len(self.project.text_to_audio_segment_map),
            'raw_text_length': len(self.project.raw_text) if self.project.raw_text else 0,
            'project_setting': asdict(self.project.project_setting) if self.project.project_setting else None
        }

    def extract_characters(self) -> Dict[str, Any]:
        """提取角色"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            self.project.extract_characters()
            self.project.save()
            return {
                'success': True,
                'characters': self.get_characters(),
                'message': f'Extracted {len(self.project.character_manager.characters)} characters'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_characters(self) -> List[Dict[str, Any]]:
        """获取所有角色"""
        if not self.project:
            return []

        characters = []
        for char in self.project.character_manager.characters:
            characters.append({
                'name': char.name,
                'description': char.description,
                'requires_tts': char.requires_tts,
                'voice_name': char.voice_name
            })
        return characters

    def update_character(self, character_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新角色信息"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            character = self.project.character_manager.get_character(character_name)
            if not character:
                return {'success': False, 'error': f'Character {character_name} not found'}

            # 应用更新
            if 'description' in updates:
                self.project.set_character_description(character_name, updates['description'])
            if 'requires_tts' in updates:
                self.project.set_character_requires_tts(character_name, updates['requires_tts'])
            if 'voice_name' in updates:
                self.project.set_character_voice_name(character_name, updates['voice_name'])

            self.project.save()
            return {'success': True, 'character': self._character_to_dict(character)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """更新项目设置"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            # 更新项目设置字段
            for key, value in settings.items():
                if hasattr(self.project.project_setting, key):
                    setattr(self.project.project_setting, key, value)
                else:
                    # 忽略未知字段
                    print(f"Warning: Unknown setting field '{key}' ignored")

            # 如果voice相关设置发生变化，更新voice_manager路径
            voice_related_keys = ['voice_lib_folder_path', 'design_model_path', 'clone_model_path', 'use_flash_attention']
            if any(key in settings for key in voice_related_keys):
                self.project.voice_manager.voice_lib_folder_path = self.project.project_setting.voice_lib_folder_path
                self.project.voice_manager.model_manager = self.project.voice_manager.model_manager.__class__(
                    self.project.project_setting.design_model_path,
                    self.project.project_setting.clone_model_path,
                    self.project.project_setting.use_flash_attention
                )

            # 保存项目
            self.project.save()
            return {'success': True, 'message': 'Settings updated successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_character(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加新角色"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            character = Character(
                name=character_data['name'],
                description=character_data.get('description', ''),
                requires_tts=character_data.get('requires_tts', False),
                voice_name=character_data.get('voice_name', '')
            )
            self.project.add_character(character)
            self.project.save()
            return {'success': True, 'character': self._character_to_dict(character)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_character(self, character_name: str) -> Dict[str, Any]:
        """删除角色"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            self.project.remove_character(character_name)
            self.project.save()
            return {'success': True, 'message': f'Character {character_name} deleted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_character_description(self, character_name: str, suggestion: str = "") -> Dict[str, Any]:
        """生成角色描述"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            # 获取项目的原始文本
            if not self.project.raw_text:
                return {'success': False, 'error': 'No text available in project'}

            # 调用 generate_character_description 方法
            description = self.project.generate_character_description(
                name=character_name,
                suggestion=suggestion
            )

            # 保存项目状态
            self.project.save()

            return {
                'success': True,
                'character_name': character_name,
                'description': description
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_text_segments(self) -> List[Dict[str, Any]]:
        """获取所有文本片段"""
        if not self.project:
            return []

        segments = []
        for i, segment in enumerate(self.project.text_manager.data):
            segments.append({
                'index': i,
                'content': segment.content,
                'tag': segment.tag,
                'allocated_speaker': self.project.text_manager.allocation_map.get(i),
                'has_audio': i in self.project.text_to_audio_segment_map
            })
        return segments

    def allocate_dialogues(self) -> Dict[str, Any]:
        """自动分配对话"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            self.project.generate_quote_allocation()
            self.project.save()
            return {
                'success': True,
                'allocated_count': len(self.project.text_manager.allocation_map),
                'segments': self.get_text_segments()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_dialogue_allocation(self, segment_index: int, speaker: str) -> Dict[str, Any]:
        """更新单个对话分配"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            self.project.set_quote_allocation(segment_index, speaker)
            self.project.save()
            return {'success': True, 'segment': self.get_text_segments()[segment_index]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_voice_designs(self) -> Dict[str, Any]:
        """生成语音设计"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            self.project.generate_voice_design()
            self.project.save()
            return {
                'success': True,
                'message': 'Voice designs generated',
                'voice_designs': self.get_voice_designs()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_voice_designs(self) -> List[Dict[str, Any]]:
        """获取语音设计"""
        if not self.project:
            return []

        designs = []
        for vd in self.project.voice_manager.voice_designs:
            designs.append({
                'name': vd.name,
                'tts_instruction': vd.tts_instruction,
                'reference_text': vd.reference_text,
                'has_reference_audio': bool(vd.reference_audio_path and os.path.exists(vd.reference_audio_path))
            })
        return designs

    def generate_audio(self) -> Dict[str, Any]:
        """生成音频"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            # 开始生成音频
            self.project.generate_text_to_audio_segment()
            self.project.save()

            # 检查生成状态
            not_generated = self.project.not_yet_generated_segments()
            generated_count = len(self.project.text_manager.data) - len(not_generated)

            return {
                'success': True,
                'generated_count': generated_count,
                'total_count': len(self.project.text_manager.data),
                'not_generated': not_generated,
                'segments': self.get_text_segments()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def render_final_audio(self) -> Dict[str, Any]:
        """渲染最终音频"""
        if not self.project:
            return {'success': False, 'error': 'Project not loaded'}

        try:
            success = self.project.render_audio()
            if success:
                final_audio_path = os.path.join(self.project_path, 'final_audio.wav')
                return {
                    'success': True,
                    'final_audio_path': final_audio_path,
                    'message': 'Final audio rendered successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to render final audio'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _character_to_dict(self, character: Character) -> Dict[str, Any]:
        """将Character对象转换为字典"""
        return {
            'name': character.name,
            'description': character.description,
            'requires_tts': character.requires_tts,
            'voice_name': character.voice_name
        }


# 工具函数
def format_error_response(error: Exception) -> Dict[str, Any]:
    """格式化错误响应"""
    return {
        'success': False,
        'error': str(error),
        'error_type': error.__class__.__name__
    }
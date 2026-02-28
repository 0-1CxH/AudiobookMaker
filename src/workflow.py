import os
import json
from dataclasses import dataclass, asdict
from .character import CharacterManager, Character
from .text import TextManager, TaggedTextSegment
from .voice import VoiceManager, VoiceDesign


WORKSPACE_PATH = os.environ.get("WORKSPACE_PATH", "./workspace")

@dataclass
class ProjectSetting:
    split_format: str = "line"
    quote_format: str = "auto"
    context_window: int = 10
    voice_lib_folder_path: str = os.path.join(WORKSPACE_PATH, "voice_lib")
    design_model_path: str = os.path.join(WORKSPACE_PATH, "design_model")
    clone_model_path: str = os.path.join(WORKSPACE_PATH, "clone_model")
    use_flash_attention: bool = False
    default_duration: float = 0.2
    line_break_duration: float = 0.5
    sentence_margin_duration: float = 0.3


class Project:
    def __init__(self, name: str, raw_text: str = "", project_setting: ProjectSetting = None) -> None:
        self.name = name
        self.project_path = os.path.join(WORKSPACE_PATH, "projects", name)
        os.makedirs(self.project_path, exist_ok=True)
        self.project_setting = project_setting if project_setting is not None else ProjectSetting()
        self.raw_text = raw_text
        self.text_manager = TextManager() if not raw_text else TextManager.convert_from_raw_text(
            text=raw_text,
            split_format=self.project_setting.split_format,
            quote_format=self.project_setting.quote_format
        )
        self.character_manager = CharacterManager()
        self.character_manager.add_character(
            Character(name="默认", description="旁白叙述", requires_tts=True, voice_name="默认")
        )
        self.voice_manager = VoiceManager(
            self.project_setting.voice_lib_folder_path,
            self.project_setting.design_model_path,
            self.project_setting.clone_model_path,
            self.project_setting.use_flash_attention
        )
        self.text_to_audio_segment_map = {}
        self.voice_artifacts_path = os.path.join(self.project_path, "voice_artifacts")
        os.makedirs(self.voice_artifacts_path, exist_ok=True)

    @classmethod
    def load(cls, name: str):
        """从磁盘加载项目"""
        project_path = os.path.join(WORKSPACE_PATH, "projects", name)
        metadata_path = os.path.join(project_path, "project_metadata.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"项目元数据文件不存在: {metadata_path}")

        # 创建空项目
        project = cls(name, raw_text="")

        # 加载元数据
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 恢复ProjectSetting
        project.project_setting = ProjectSetting(**metadata.get('project_setting', {}))

        # 恢复原始文本
        project.raw_text = metadata.get('raw_text', '')

        # 恢复文本管理器
        text_data = metadata.get('text_manager', {})
        if text_data:
            project.text_manager.data = [
                TaggedTextSegment(content=seg['content'], tag=seg['tag'])
                for seg in text_data.get('data', [])
            ]
            project.text_manager.allocation_map = text_data.get('allocation_map', {})

        # 恢复人物管理器
        characters_data = metadata.get('character_manager', {}).get('characters', [])
        project.character_manager.characters = [
            Character(
                name=char['name'],
                description=char['description'],
                requires_tts=char['requires_tts'],
                voice_name=char['voice_name']
            )
            for char in characters_data
        ]

        # 恢复语音管理器
        voice_designs_data = metadata.get('voice_manager', {}).get('voice_designs', [])
        project.voice_manager.voice_designs = [
            VoiceDesign(
                name=vd['name'],
                tts_instruction=vd['tts_instruction'],
                reference_text=vd.get('reference_text', ''),
                reference_audio_path=vd.get('reference_audio_path')
            )
            for vd in voice_designs_data
        ]

        # 恢复音频片段映射
        project.text_to_audio_segment_map = {
            int(k): v for k, v in metadata.get('text_to_audio_segment_map', {}).items()
        }

        # 重新设置语音管理器的路径（因为它们可能在ProjectSetting中已更改）
        project.voice_manager.voice_lib_folder_path = project.project_setting.voice_lib_folder_path
        project.voice_manager.model_manager = project.voice_manager.model_manager.__class__(
            project.project_setting.design_model_path,
            project.project_setting.clone_model_path,
            project.project_setting.use_flash_attention
        )

        return project

    def save(self):
        """保存项目到磁盘"""
        # 确保项目目录存在
        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(self.voice_artifacts_path, exist_ok=True)

        # 构建元数据字典
        metadata = {
            'name': self.name,
            'project_setting': asdict(self.project_setting),
            'raw_text': self.raw_text,
            'text_manager': {
                'data': [
                    {'content': seg.content, 'tag': seg.tag}
                    for seg in self.text_manager.data
                ],
                'allocation_map': self.text_manager.allocation_map
            },
            'character_manager': {
                'characters': [
                    {
                        'name': char.name,
                        'description': char.description,
                        'requires_tts': char.requires_tts,
                        'voice_name': char.voice_name
                    }
                    for char in self.character_manager.characters
                ]
            },
            'voice_manager': {
                'voice_designs': [
                    {
                        'name': vd.name,
                        'tts_instruction': vd.tts_instruction,
                        'reference_text': vd.reference_text,
                        'reference_audio_path': vd.reference_audio_path
                    }
                    for vd in self.voice_manager.voice_designs
                ]
            },
            'text_to_audio_segment_map': self.text_to_audio_segment_map
        }

        # 保存元数据文件
        metadata_path = os.path.join(self.project_path, "project_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 保存原始文本到单独文件（可选）
        raw_text_path = os.path.join(self.project_path, "raw_text.txt")
        with open(raw_text_path, 'w', encoding='utf-8') as f:
            f.write(self.raw_text)

        print(f"项目 '{self.name}' 已保存到 {self.project_path}")
        return True

    def extract_characters(self):
        self.character_manager.extract_characters_from_raw_text(text=self.raw_text)

    def add_character(self, character: Character):
        self.character_manager.add_character(character)

    def remove_character(self, character_name: str):
        self.character_manager.remove_character(character_name)
        self.text_manager.remove_speaker_tags_by_name(character_name)
        self.remove_audio_segments_by_character(character_name)

    def get_character_names(self):
        return self.character_manager.get_all_character_descriptions(name_only=True)

    def get_character_voice_names_and_descriptions(self):
        return self.character_manager.get_all_character_descriptions(name_only=False, use_voice_name=True)

    def set_character_description(self, name: str, description: str):
        self.character_manager.set_character_description(name, description)

    def set_character_voice_name(self, name: str, voice_name: str):
        self.character_manager.set_character_voice_name(name, voice_name)

    def set_character_requires_tts(self, name: str, requires_tts: bool):
        self.character_manager.set_character_requires_tts(name, requires_tts)

    def generate_character_description(self, name: str, suggestion: str = ""):
        return self.character_manager.generate_character_description(
            text=self.raw_text,
            character_name=name,
            suggestion=suggestion
        )

    def set_quote_allocation(self, segment_index: int, speaker: str):
        assert speaker in self.get_character_names(), f"人物 {speaker} 不存在"
        self.text_manager.set_speaker_tag(segment_index, speaker)

    def remove_quote_allocation(self, segment_index: int):
        self.text_manager.set_speaker_tag(segment_index, TextManager.QUOTE_TAG)

    def generate_quote_allocation(self):
        character_names = self.get_character_names()
        assert character_names, "未找到任何人物，请先提取或添加人物"
        self.text_manager.allocate_quote_to_character(character_names, self.project_setting.context_window)

    def set_voice_design_tts_instruction(self, voice_name: str, instruction: str):
        self.voice_manager.set_voice_design_tts_instruction(voice_name, instruction)

    def set_voice_design_reference_text(self, voice_name: str, text: str):
        self.voice_manager.set_voice_design_reference_text(voice_name, text)

    def generate_voice_design(self):
        character_voice_names_and_descriptions = self.get_character_voice_names_and_descriptions()
        assert character_voice_names_and_descriptions, "未找到任何需要TTS的人物，先设置需要TTS的人物"
        for voice_name, description in character_voice_names_and_descriptions.items():
            self.voice_manager.create_from_character_description(voice_name, description)

    def generate_reference_audio(self, character_name: str = None):
        if character_name:
            character = self.character_manager.get_character(character_name)
            assert character, f"人物 {character_name} 不存在"
            if character.requires_tts:
                self.voice_manager.generate_reference_audio(character.voice_name)
            else:
                print(f"人物 {character_name} 不需要TTS，跳过")
        else:
            character_voice_names_and_descriptions = self.get_character_voice_names_and_descriptions()
            assert character_voice_names_and_descriptions, "未找到任何需要TTS的人物，先设置需要TTS的人物"
            for voice_name, description in character_voice_names_and_descriptions.items():
                self.voice_manager.generate_reference_audio(voice_name)

    def generate_text_to_audio_segment(self):
        """将文本片段转换为音频片段

        处理规则：
        1. QUOTE_TAG: 找到对应人物，获取voice_name，使用voice_manager.generate_voice生成音频
        2. DEFAULT_TAG: 使用默认人物（已初始化在character_manager中）
        3. PLACEHOLDER_TAG: 暂时用pass处理，将来生成空白音频

        生成的音频文件保存到voice_artifacts_path目录，对应关系存储到text_to_audio_segment_map中，
        支持断点续执行（已生成过的片段跳过）
        """
        # 获取默认人物
        default_character = self.character_manager.get_character("默认")
        if not default_character:
            print("错误：默认人物不存在，请确保已初始化默认人物")
            return

        for i, segment in enumerate(self.text_manager.data):
            # 如果已经生成过，跳过
            if i in self.text_to_audio_segment_map:
                continue

            tag = segment.tag
            content = segment.content
            audio_file_name = f"segment_{i}.wav"
            audio_file_path = os.path.join(self.voice_artifacts_path, audio_file_name)

            if tag == TextManager.QUOTE_TAG:
                # QUOTE_TAG: 标签本身是人物名字，需要找到对应的人物
                character_name = tag  # tag就是人物名字
                character = self.character_manager.get_character(character_name)

                if not character:
                    print(f"警告：人物 '{character_name}' 不存在，跳过生成")
                    continue # 不写入，标记未处理

                # 检查人物是否需要TTS，如果不需要则跳过
                if not character.requires_tts:
                    print(f"信息：人物 '{character_name}' 不需要TTS，跳过生成")
                    continue # 不写入，标记未处理

                # 获取人物的voice_name
                voice_name = character.voice_name
                if not voice_name:
                    print(f"警告：人物 '{character_name}' 没有设置voice_name，使用默认voice")
                    voice_name = default_character.voice_name

                # 生成音频
                try:
                    self.voice_manager.generate_voice(voice_name, content, audio_file_path)
                    self.text_to_audio_segment_map[i] = audio_file_path
                    print(f"已生成QUOTE音频片段 {i}: {character_name} -> {audio_file_name}")
                except Exception as e:
                    print(f"生成QUOTE音频失败 (片段 {i}): {e}")

            elif tag == TextManager.DEFAULT_TAG:
                # DEFAULT_TAG: 使用默认人物
                voice_name = default_character.voice_name
                if not voice_name:
                    print("错误：默认人物没有设置voice_name")
                    continue # 不写入，标记未处理

                # 生成音频
                try:
                    self.voice_manager.generate_voice(voice_name, content, audio_file_path)
                    self.text_to_audio_segment_map[i] = audio_file_path
                    print(f"已生成DEFAULT音频片段 {i}: 默认 -> {audio_file_name}")
                except Exception as e:
                    print(f"生成DEFAULT音频失败 (片段 {i}): {e}")

            elif tag == TextManager.PLACEHOLDER_TAG:
                # PLACEHOLDER_TAG: 生成空白音频
                # 根据不同占位符类型设置不同时长

                if content == '\n':
                    duration = self.project_setting.line_break_duration  # 换行符
                elif content in ['。', '！', '？', '.', '!', '?']:
                    duration = self.project_setting.sentence_margin_duration  # 句末标点
                else:
                    duration = self.project_setting.default_duration

                # 生成空白音频并保存
                try:
                    wavs, sr = self.voice_manager.model_manager.generate_blank_audio(duration=duration)
                    # 确保是列表或数组格式
                    if not isinstance(wavs, list):
                        wavs = [wavs]
                    self.voice_manager.model_manager.write_voice_to_file(wavs, sr, audio_file_path)
                    self.text_to_audio_segment_map[i] = audio_file_path
                    print(f"已生成PLACEHOLDER空白音频片段 {i} ({duration}秒): {audio_file_name}")
                except Exception as e:
                    print(f"生成PLACEHOLDER空白音频失败 (片段 {i}): {e}")

            else:
                # 其他未知标签
                print(f"警告：未知标签 '{tag}' (片段 {i})，跳过")

    def not_yet_generated_segments(self):
        return [i for i in range(len(self.text_manager.data)) if i not in self.text_to_audio_segment_map]

    def remove_audio_segments_by_index(self, segment_indices):
        """删除指定索引的音频片段

        Args:
            segment_indices: 要删除的片段索引列表或单个索引
        """
        if not isinstance(segment_indices, list):
            segment_indices = [segment_indices]

        for i in segment_indices:
            if i in self.text_to_audio_segment_map:
                audio_file_path = self.text_to_audio_segment_map[i]
                # 删除文件
                try:
                    if os.path.exists(audio_file_path):
                        os.remove(audio_file_path)
                        print(f"已删除音频文件: {audio_file_path}")
                except Exception as e:
                    print(f"删除音频文件失败 (片段 {i}): {e}")
                # 从映射中删除
                del self.text_to_audio_segment_map[i]
                print(f"已移除片段 {i} 的音频映射")

    def remove_audio_segments_by_character(self, character_name):
        """删除指定人物相关的所有音频片段

        Args:
            character_name: 人物名字
        """
        character = self.character_manager.get_character(character_name)
        if not character:
            print(f"警告：人物 '{character_name}' 不存在")
            return

        # 找到所有标记为该人物的片段索引
        indices_to_remove = []
        for i, segment in enumerate(self.text_manager.data):
            if segment.tag == character_name:
                indices_to_remove.append(i)

        # 删除这些片段的音频
        self.remove_audio_segments_by_index(indices_to_remove)
        print(f"已删除人物 '{character_name}' 相关的 {len(indices_to_remove)} 个音频片段")

    def render_audio(self):
        """生成最终的音频文件

        检查是否还有未生成的音频片段，如果没有，则拼接所有已生成的音频片段
        """
        # 检查是否还有未生成的音频片段
        not_generated = self.not_yet_generated_segments()
        if not_generated:
            print(f"还有 {len(not_generated)} 个片段未生成音频，无法渲染最终音频")
            return False

        # 获取所有已生成的音频片段路径，按照索引从小到大排序
        all_segments = sorted(self.text_to_audio_segment_map.keys())
        audio_paths = [self.text_to_audio_segment_map[i] for i in all_segments]

        # 设置输出文件路径
        output_file = os.path.join(self.project_path, "final_audio.wav")

        # 导入concatenate_audio_files函数
        from .utils import concatenate_audio_files

        # 拼接音频文件
        success = concatenate_audio_files(audio_paths, output_file)

        if success:
            print(f"最终音频文件已生成: {output_file}")
        else:
            print("最终音频文件生成失败")

        return success
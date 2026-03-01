import os
from dataclasses import dataclass
from .utils import single_llm_request, LocalQwen3TTSModelManager

@dataclass
class VoiceDesign:
    name: str
    tts_instruction: str
    reference_text: str = '''北风和太阳正在争论谁更强大，这时一个旅人走了过来，身上裹着一件厚厚的外套。他们约定，谁能先让旅人脱下外套，谁就是更强的一方。
于是北风拼命地吹，可他吹得越猛烈，旅人就把外套裹得越紧。最后北风无奈地放弃了。
接着太阳温暖地照耀起来，没过多久，旅人便感到炎热，主动脱下了外套。就这样，北风不得不承认，太阳才是更强的那一个。'''
    reference_audio_path: str = None

    @classmethod
    def create_from_character_description(cls, voice_name: str, character_description: str):
        """根据人物小传生成TTS指令

        Args:
            character_description: 人物小传描述

        Returns:
            VoiceDesign: 生成的音色设计对象，包含LLM生成的tts_instruction
        """
        

        # 构造LLM提示词
        prompt = f"""请根据以下人物小传，为TTS模型生成语音控制指令。

人物小传：
{character_description}

请生成详细的TTS音色控制指令，包括音色特点、语调、语速、情感等。
指令是自然语言描述，需要能够指导模型生成符合该人物性格和特点的语音。
请直接返回指令文本，不要添加任何额外的说明或格式。
"""

        try:
            print(f"生成声音设计 {voice_name} 的TTS指令中...")
            # 调用LLM
            tts_instruction = single_llm_request(prompt=prompt).strip()
            
            return cls(
                name=voice_name,
                tts_instruction=tts_instruction,
            )

        except Exception as e:
            print(f"生成TTS指令失败: {e}")
            return None


class VoiceManager:
    def __init__(self, voice_lib_folder_path, design_model_path, clone_model_path, use_flash_attention):
        self.voice_designs = []
        self.voice_lib_folder_path = voice_lib_folder_path
        os.makedirs(self.voice_lib_folder_path, exist_ok=True)
        self.model_manager = LocalQwen3TTSModelManager(
            design_model_path,
            clone_model_path,
            use_flash_attention
        )
    
    def add_voice_design(self, voice_name: str, tts_instruction: str):
        voice_design = self.get_voice_design(voice_name)
        if voice_design:
            voice_design.tts_instruction = tts_instruction
            voice_design.reference_audio_path = None # the file still exists, but it means it's invalid
        else:
            self.voice_designs.append(VoiceDesign(voice_name, tts_instruction))
        return True
    
    def create_from_character_description(self, voice_name: str, character_description: str):
        voice_design = VoiceDesign.create_from_character_description(voice_name, character_description)
        if not voice_design:
            return False
        return self.add_voice_design(voice_name, voice_design.tts_instruction)

    
    def remove_voice_design(self, voice_name: str):
        self.voice_designs = [voice_design for voice_design in self.voice_designs if voice_design.name != voice_name]
    
    def get_voice_design(self, voice_name: str):
        for voice_design in self.voice_designs:
            if voice_design.name == voice_name:
                return voice_design
        return None
    
    def set_voice_design_tts_instruction(self, voice_name: str, tts_instruction: str):
        for voice_design in self.voice_designs:
            if voice_design.name == voice_name:
                voice_design.tts_instruction = tts_instruction
                voice_design.reference_audio_path = None # the file still exists, but it means it's invalid
                return True
        return False
    
    def set_voice_design_reference_text(self, voice_name: str, reference_text: str):
        for voice_design in self.voice_designs:
            if voice_design.name == voice_name:
                voice_design.reference_text = reference_text
                voice_design.reference_audio_path = None # the file still exists, but it means it's invalid
                return True
        return False
    
    def set_voice_design_reference_audio_path(self, voice_name: str, reference_audio_path: str):
        for voice_design in self.voice_designs:
            if voice_design.name == voice_name:
                voice_design.reference_audio_path = reference_audio_path
                return True
        return False
    
    def generate_reference_audio(self, voice_name: str):
        voice_design = self.get_voice_design(voice_name)
        if not voice_design:
            return None
        wavs, sr = self.model_manager.generate_voice_design(
            text=voice_design.reference_text,
            instruct=voice_design.tts_instruction
        )
        reference_audio_path = os.path.join(self.voice_lib_folder_path, f"{voice_name}.wav")
        self.model_manager.write_voice_to_file(
            wavs, sr, reference_audio_path
        )
        self.set_voice_design_reference_audio_path(voice_name, reference_audio_path)
    
    def generate_voice(self, voice_name: str, text: str, voice_save_path: str):
        voice_design = self.get_voice_design(voice_name)
        if not voice_design:
            return None
        wavs, sr = self.model_manager.generate_voice_clone(
            text=text,
            ref_audio_path=voice_design.reference_audio_path,
            ref_text=voice_design.reference_text,
            instruct=voice_design.tts_instruction
        )
        self.model_manager.write_voice_to_file(
            wavs, sr, voice_save_path
        )

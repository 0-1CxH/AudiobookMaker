import os
import openai
import json
import re
import torch
import soundfile as sf
import functools
import numpy as np
from qwen_tts import Qwen3TTSModel

def single_llm_request(**kwargs):
    """使用OpenAI SDK进行LLM请求"""
    api_key = kwargs.get('api_key') or os.environ.get('LLM_API_KEY')
    api_base = kwargs.get('api_url') or os.environ.get('LLM_API_URL')
    model = kwargs.get('model') or os.environ.get('LLM_MODEL')

    client = openai.OpenAI(
        api_key=api_key,
        base_url=api_base,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": kwargs['prompt']}
        ],
        n=1
    )

    return response.choices[0].message.content

def extract_json(s):
    json_data = None
    try:
        # Try to extract JSON content from code block
        if "```json" in s and "```" in s.split("```json", 1)[1]:
            json_content = s.split("```json", 1)[1].split("```")[0].strip()
        elif "<json>" in s and "</json>" in s.split("</json>", 1)[1]:
            json_content = s.split("</json>", 1)[1].split("</json>")[0].strip()
        elif "```" in s:
            # Try to extract from any code block
            json_content = s.split("```", 2)[1].strip()
        else:
            json_content = s.strip()
        
        # Safely parse JSON
        json_data = json.loads(json_content)
        
        if not isinstance(json_data, dict):
            json_data = {"result": json_data}
    except json.JSONDecodeError:
        # if can not decode, try extract using regex
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, s)
        if matches:
            json_data = json.loads(matches[0])
        else:
            # if everything fails, create a dict of str s
            json_data = {"response": s}
    return json_data

class LocalQwen3TTSModelManager:
    _instance = None
    _design_model = None
    _clone_model = None
    _design_model_path = None
    _clone_model_path = None
    _use_flash_attention = False
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, design_model_path: str = None, clone_model_path: str = None, use_flash_attention: bool = False):
        if not self._initialized:
            self._design_model_path = design_model_path
            self._clone_model_path = clone_model_path
            self._use_flash_attention = use_flash_attention
            self._initialized = True

    def _load_model(self, model_path: str, model_type: str):
        """加载指定类型的模型"""
        if model_path:
            model = Qwen3TTSModel.from_pretrained(
                model_path,
                device_map="cuda:0",
                dtype=torch.bfloat16,
                attn_implementation="flash_attention_2" if self._use_flash_attention else None,
            )

            if model_type == "design":
                self._design_model = model
                return self._design_model
            elif model_type == "clone":
                self._clone_model = model
                return self._clone_model

        return None

    def get_design_model(self):
        """获取设计模型，如果未加载则加载"""
        if self._design_model is None and self._design_model_path:
            return self._load_model(self._design_model_path, "design")
        return self._design_model

    def get_clone_model(self):
        """获取克隆模型，如果未加载则加载"""
        if self._clone_model is None and self._clone_model_path:
            return self._load_model(self._clone_model_path, "clone")
        return self._clone_model

    @property
    def design_model(self):
        """设计模型属性"""
        return self.get_design_model()

    @property
    def clone_model(self):
        """克隆模型属性"""
        return self.get_clone_model()

    @property
    def design_model_path(self):
        return self._design_model_path

    @property
    def clone_model_path(self):
        return self._clone_model_path

    @property
    def use_flash_attention(self):
        return self._use_flash_attention
    
    def generate_voice_design(self, text: str, instruct: str):
        wavs, sr = self.design_model.generate_voice_design(
            text=text,
            language="Chinese",
            instruct= instruct,
            do_sample=False,
        )
        return wavs, sr
    
    @functools.lru_cache(maxsize=128)
    def create_clone_prompt(self, ref_audio_path: str, ref_text: str):
        """生成语音克隆提示，使用LRU缓存最近128个不同的音频-文本组合

        Args:
            ref_audio_path: 参考音频文件路径
            ref_text: 参考文本内容

        Returns:
            voice_clone_prompt: 语音克隆提示
        """
        voice_clone_prompt = self.clone_model.create_voice_clone_prompt(
            ref_audio=ref_audio_path,
            ref_text=ref_text,
        )
        return voice_clone_prompt
    
    def generate_voice_clone(self, text: str, ref_audio_path: str, ref_text: str, instruct: str):
        voice_clone_prompt = self.create_clone_prompt(ref_audio_path, ref_text)
        wavs, sr = self.clone_model.generate_voice_clone(
            text=text,
            language="Chinese",
            voice_clone_prompt=voice_clone_prompt,
            instruct=instruct,
        )
        return wavs, sr
    
    def generate_blank_audio(self, duration: float = 1.0, sample_rate: int = 24000):
        """生成空白音频文件

        Args:
            duration: 音频时长（秒）
            sample_rate: 采样率
        """
        # 生成静音数据（全零）
        samples = int(duration * sample_rate)
        silent_data = np.zeros(samples, dtype=np.float32)
        return silent_data, sample_rate
    
    def write_voice_to_file(self, wavs, sr, output_path: str):
        if len(wavs) == 1:
            sf.write(output_path, wavs[0], sr)
        else:
            for i, wav in enumerate(wavs):
                sf.write(f"{output_path.replace('.wav', '')}_{i}.wav", wav, sr)

def concatenate_audio_files(input_paths: list[str], output_path: str, sample_rate: int = 24000):
    """将若干音频文件拼接成一个音频文件

    Args:
        input_paths: 输入音频文件路径列表，按顺序拼接
        output_path: 输出音频文件路径
        sample_rate: 采样率，默认为24000（与Qwen TTS默认采样率一致）

    Returns:
        bool: 拼接是否成功
    """
    try:
        audio_data_list = []

        # 读取所有音频文件
        for input_path in input_paths:
            if not os.path.exists(input_path):
                print(f"警告：音频文件不存在 {input_path}")
                continue

            data, sr = sf.read(input_path)

            # 检查采样率是否一致
            if sr != sample_rate:
                print(f"警告：文件 {input_path} 的采样率 {sr} 与目标采样率 {sample_rate} 不一致")
                # 这里可以选择重采样，但为了简单起见，我们只记录警告

            audio_data_list.append(data)

        if not audio_data_list:
            print("错误：没有有效的音频文件可拼接")
            return False

        # 拼接音频数据
        concatenated_data = np.concatenate(audio_data_list)

        # 写入输出文件
        sf.write(output_path, concatenated_data, sample_rate)

        print(f"成功拼接 {len(audio_data_list)} 个音频文件到 {output_path}")
        return True

    except Exception as e:
        print(f"拼接音频文件失败: {e}")
        return False

    
from dataclasses import dataclass

@dataclass
class Voice:
    name: str
    tts_instruction: str
    reference_text: str
    reference_audio_path: str

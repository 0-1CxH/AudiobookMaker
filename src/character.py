from dataclasses import dataclass

@dataclass
class Character:
    name: str
    description: str = ""
    requires_tts: bool = False
    voice_id: str = ""


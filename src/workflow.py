from dataclasses import dataclass
from .character import CharacterManager, Character
from .text import TextManager


@dataclass
class ProjectSetting:
    split_format: str = "line"
    quote_format: str = "auto"
    context_window: int = 10


class Project:
    def __init__(self, name: str, raw_text: str) -> None:
        self.name = name
        self.project_setting = ProjectSetting()
        self.raw_text = raw_text
        self.text_manager = TextManager.convert_from_raw_text(
            text=raw_text,
            split_format=self.project_setting.split_format,
            quote_format=self.project_setting.quote_format
        )
        self.character_manager = CharacterManager()
        self.voice_manager = None
        
    
    def extract_characters(self):
        self.character_manager.extract_characters_from_raw_text(text=self.raw_text)
    
    def add_character(self, character: Character):
        self.character_manager.add_character(character)
    
    def remove_character(self, name: str):
        self.character_manager.remove_character(name)
        # also remove its tag in text manager
    
    def generate_character_description(self, name: str, suggestion: str = ""):
        self.character_manager.generate_character_description(
            text=self.raw_text,
            character_name=name,
            suggestion=suggestion
        )
    
    def quote_allocation(self):
        character_names = self.character_manager.get_all_character_descriptions(name_only=True)
        assert character_names, "未找到任何人物，请先提取或添加人物"
        self.text_manager.allocate_quote_to_character(character_names, self.project_setting.context_window)

    

    

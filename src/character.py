from dataclasses import dataclass
from .utils import single_llm_request, extract_json

@dataclass
class Character:
    name: str
    description: str = ""
    requires_tts: bool = False
    voice_name: str = ""

class CharacterManager:
    def __init__(self) -> None:
        self.characters = []

    def add_character(self, character: Character):
        if self.get_character(character.name):
            return
        self.characters.append(character)

    def get_character(self, name: str):
        for character in self.characters:
            if character.name == name:
                return character
        return None

    @classmethod
    def extract_characters_from_raw_text(cls, text: str):
        """从原始文本中提取人物名字和描述

        Args:
            text: 原始文本

        Returns:
            list[Character]: 提取到的人物对象列表
        """
        # 构造LLM提示词
        prompt = f"""请分析以下文本，提取出所有重要的人物角色。对于每个人物，提供：
        1. 人物名字（name）
        2. 人物小传（description）：简要描述人物的特点、性格、背景等关键特征，以及简要生平（如果有的话）。注意不要添加文本中没有的信息。

        文本内容：
        {text}

        请以JSON格式返回结果，格式如下：
        {{
            "characters": [
                {{
                    "name": "人物名字",
                    "description": "人物小传"
                }}
            ]
        }}
        """

        # 调用LLM
        try:
            response = single_llm_request(
                prompt=prompt
            )

            # 提取JSON
            result = extract_json(response)

            # 解析结果为Character对象列表
            characters = []
            if isinstance(result, dict) and "characters" in result:
                for char_data in result["characters"]:
                    if "name" in char_data:
                        description = char_data.get("description", "")
                        # 创建Character对象，requires_tts和voice_name保持默认
                        character = Character(
                            name=char_data["name"],
                            description=description,
                            requires_tts=False,
                            voice_name=""
                        )
                        characters.append(character)

            return characters

        except Exception as e:
            print(f"提取人物失败: {e}")
            return []
    
    def generate_character_description(self, text: str, character_name: str, suggestion: str = ""):
        """生成指定人物的小传描述

        Args:
            text: 原始文本
            character_name: 要生成描述的人物名字
            suggestion: 可选的建议描述

        Returns:
            str: 生成的人物小传描述，如果失败则返回空字符串
        """
        # 构造LLM提示词
        prompt = f"""请分析以下文本，为指定人物生成人物小传。

        人物名字：{character_name}

        文本内容：
        {text}

        {"参考以下要求：" + suggestion if suggestion else ""}

        请专注于这个人物，基于文本内容生成人物小传。
        描述应包括人物的特点、性格、背景等关键特征，以及简要生平（如果有的话）。注意不要添加文本中没有的信息。

        请直接返回人物小传的文本描述，不需要JSON格式，不需要额外的说明。
        """

        # 调用LLM
        try:
            response = single_llm_request(
                prompt=prompt
            )

            # 返回清理后的描述
            description = response.strip()

            # 尝试查找并更新已有的人物对象
            character = self.get_character(character_name)
            if character:
                character.description = description
            else:
                # 如果人物不存在，创建一个新的人物对象
                character = Character(
                    name=character_name,
                    description=description,
                    requires_tts=False,
                    voice_name=""
                )
                self.add_character(character)

            return description

        except Exception as e:
            print(f"生成人物描述失败: {e}")
            return ""
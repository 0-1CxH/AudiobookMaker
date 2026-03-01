import os
import pytest
from src.character import CharacterManager, Character


class TestCharacterExtraction:
    """测试人物提取功能"""

    def test_extract_characters(self):
        """测试从文本中提取人物"""
        # 测试文本 - 一个简单的小说片段
        test_text = """
        在一个遥远的王国里，有一位勇敢的王子名叫阿尔文。
        他有着金色的头发和蓝色的眼睛，性格坚毅勇敢。

        王子的朋友是魔法师梅林，他是一位智慧的老者。
        梅林总是帮助阿尔文解决各种难题，他有着长长的白胡子和深邃的眼神。

        王国里还有一个邪恶的巫师名叫马尔福。
        马尔福总是试图破坏王国的和平，他性格阴险狡诈。

        有一天，阿尔文对梅林说："我们需要找到传说中的宝剑。"
        梅林回答道："是的，那把宝剑在遥远的龙之谷。"
        """

        # 提取人物
        cm = CharacterManager()
        cm.extract_characters_from_raw_text(test_text)

        # 验证提取结果
        assert len(cm.characters) > 0

        # 验证每个人物都有名字和描述
        for char in cm.characters:
            assert isinstance(char, Character)
            assert char.name
            assert isinstance(char.description, str)
            assert char.requires_tts is False  # 默认值
            assert char.voice_name == ""  # 默认值

        # 检查是否包含预期的关键人物
        character_names = [char.name for char in cm.characters]
        # 阿尔文、梅林、马尔福至少应该有一个被提取到
        expected_names = ["阿尔文", "梅林", "马尔福"]
        found_expected = any(name in character_names for name in expected_names)
        assert found_expected, f"期望至少提取到{expected_names}中的一个，实际提取到: {character_names}"


class TestCharacterDescriptionGeneration:
    """测试人物描述生成功能"""

    def setup_method(self):
        """设置测试方法前的初始化"""
        self.manager = CharacterManager()

        # 添加一个示例人物（初始描述可能比较简单）
        self.initial_character = Character(
            name="阿尔文",
            description="勇敢的王子",
            requires_tts=False,
            voice_name=""
        )
        self.manager.add_character(self.initial_character)

    def test_generate_description_for_existing_character(self):
        """测试为已存在的人物生成描述"""
        # 测试文本 - 包含阿尔文更多信息的文本
        test_text = """
        在一个遥远的王国里，有一位勇敢的王子名叫阿尔文。
        他有着金色的头发和蓝色的眼睛，性格坚毅勇敢。
        阿尔文从小接受严格的骑士训练，擅长剑术和马术。
        他的父亲是老王理查德，母亲是王后伊丽莎白。

        阿尔文的责任感很强，总是把王国和人民的利益放在第一位。
        他有一个亲密的朋友魔法师梅林，两人经常一起冒险。
        阿尔文最大的愿望是找到传说中的宝剑，保卫王国免受邪恶巫师马尔福的威胁。

        在故事中，阿尔文展现了领导才能和牺牲精神。
        他曾多次带领士兵击退入侵者，深受人民爱戴。
        他还有一颗善良的心，经常帮助穷苦的百姓。
        """

        # 生成人物描述
        new_description = self.manager.generate_character_description(test_text, "阿尔文")

        # 验证生成的描述
        assert new_description
        assert isinstance(new_description, str)
        # assert new_description != self.initial_character.description

        # 检查人物对象是否已更新
        updated_character = self.manager.get_character("阿尔文")
        assert updated_character is not None
        assert updated_character.description == new_description

    def test_generate_description_for_new_character(self):
        """测试为新人物生成描述"""
        # 测试文本
        test_text = """
        王国里还有一个邪恶的巫师名叫马尔福。
        马尔福总是试图破坏王国的和平，他性格阴险狡诈。
        马尔福住在黑暗之塔，掌握着强大的黑魔法。
        他的目标是夺取王国的控制权，统治所有人民。
        """

        # 生成人物描述（马尔福不在当前管理器中）
        new_description = self.manager.generate_character_description(test_text, "马尔福")

        # 验证生成的描述
        assert new_description
        assert isinstance(new_description, str)
        assert len(new_description) > 0

        # 检查是否创建了新的人物
        new_character = self.manager.get_character("马尔福")
        assert new_character is not None
        assert new_character.name == "马尔福"
        assert new_character.description == new_description

    def test_generate_description_with_suggestion(self):
        """测试带建议的生成人物描述"""
        test_text = """
        精灵公主莉莉娅是森林王国的守护者。
        她有着银色的长发和绿色的眼睛，擅长自然魔法。
        """

        suggestion = "请重点描述她的魔法能力和在王国中的角色"

        # 生成带建议的描述
        new_description = self.manager.generate_character_description(
            test_text, "莉莉娅", suggestion
        )

        # 验证生成的描述
        assert new_description
        assert isinstance(new_description, str)

        # 检查是否创建了新的人物
        new_character = self.manager.get_character("莉莉娅")
        assert new_character is not None
        assert new_character.name == "莉莉娅"
        assert new_character.description == new_description

    def test_generate_description_empty_text(self):
        """测试用空文本生成描述"""
        test_text = ""

        # 生成人物描述
        new_description = self.manager.generate_character_description(test_text, "测试人物")

        # 空文本可能导致空描述或失败
        # 我们不检查具体内容，只验证函数不抛出异常
        assert isinstance(new_description, str)

    def test_character_manager_add_and_get(self):
        """测试CharacterManager的添加和获取功能"""
        manager = CharacterManager()

        # 添加人物
        character1 = Character("张三", "一个程序员", False, "")
        character2 = Character("李四", "一个设计师", True, "voice1")

        manager.add_character(character1)
        manager.add_character(character2)

        # 测试获取
        assert manager.get_character("张三") == character1
        assert manager.get_character("李四") == character2
        assert manager.get_character("王五") is None

        # 测试重复添加（应该不重复添加）
        character1_duplicate = Character("张三", "另一个描述", True, "voice2")
        manager.add_character(character1_duplicate)

        # 原始character1应该保持不变
        assert manager.get_character("张三").description == "一个程序员"


@pytest.mark.skipif(
    not os.environ.get('LLM_API_URL') or not os.environ.get('LLM_API_KEY'),
    reason="需要设置LLM_API_URL和LLM_API_KEY环境变量"
)
class TestCharacterFunctionsIntegration:
    """测试人物功能的集成测试（需要实际环境变量）"""

    def test_extract_characters_real_api(self):
        """测试实际API调用的人物提取"""
        # 测试文本
        test_text = """
        在一个遥远的王国里，有一位勇敢的王子名叫阿尔文。
        他有着金色的头发和蓝色的眼睛，性格坚毅勇敢。
        """

        # 提取人物
        cm = CharacterManager()
        cm.extract_characters_from_raw_text(test_text)

        # 验证结果
        assert isinstance(cm.characters, list)
        assert len(cm.characters) > 0
        # LLM可能成功提取或失败，我们不强制要求一定提取到人物
        if cm.characters:
            for char in cm.characters:
                assert isinstance(char, Character)
                assert char.name
                assert isinstance(char.description, str)

    def test_generate_description_real_api(self):
        """测试实际API调用的人物描述生成"""
        manager = CharacterManager()

        # 测试文本
        test_text = """
        勇敢的骑士亚瑟拔出圣剑，准备与恶龙战斗。
        亚瑟是圆桌骑士的首领，以勇气和正义闻名。
        """

        # 生成描述
        description = manager.generate_character_description(test_text, "亚瑟")

        # 验证结果
        assert isinstance(description, str)
        # LLM可能返回空字符串或有效描述
        if description:
            # 检查是否创建了人物
            character = manager.get_character("亚瑟")
            assert character is not None
            assert character.name == "亚瑟"
            assert character.description == description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
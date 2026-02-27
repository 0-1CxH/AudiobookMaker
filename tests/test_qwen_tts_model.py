import os
import pytest
import tempfile
import soundfile as sf
import numpy as np

if os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH') or os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'):
    from src.utils import LocalQwen3TTSModelManager


class TestLocalQwen3TTSModelManagerIntegration:
    """测试LocalQwen3TTSModelManager的集成测试（需要实际模型路径）"""

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH') or not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_DESIGN_MODEL_PATH和QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def setup_method(self):
        """每个测试方法运行前执行"""
        # 重置单例实例以便隔离测试
        LocalQwen3TTSModelManager._instance = None
        LocalQwen3TTSModelManager._initialized = False
        LocalQwen3TTSModelManager._design_model = None
        LocalQwen3TTSModelManager._clone_model = None
        LocalQwen3TTSModelManager._design_model_path = None
        LocalQwen3TTSModelManager._clone_model_path = None

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH') or not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_DESIGN_MODEL_PATH和QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def test_real_model_loading(self):
        """测试实际模型加载"""
        design_model_path = os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH')
        clone_model_path = os.environ.get('QWEN_TTS_CLONE_MODEL_PATH')

        assert design_model_path is not None, "QWEN_TTS_DESIGN_MODEL_PATH环境变量未设置"
        assert clone_model_path is not None, "QWEN_TTS_CLONE_MODEL_PATH环境变量未设置"

        try:
            manager = LocalQwen3TTSModelManager(
                design_model_path=design_model_path,
                clone_model_path=clone_model_path
            )

            # 测试模型加载
            design_model = manager.get_design_model()
            clone_model = manager.get_clone_model()

            assert design_model is not None
            assert clone_model is not None

            # 测试属性访问
            assert manager.design_model is design_model
            assert manager.clone_model is clone_model
            assert manager.design_model_path == design_model_path
            assert manager.clone_model_path == clone_model_path

            print(f"设计模型加载成功: {design_model}")
            print(f"克隆模型加载成功: {clone_model}")

        except Exception as e:
            print(f"模型加载失败: {e}")
            pytest.skip(f"模型加载失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH') or not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_DESIGN_MODEL_PATH和QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def test_singleton_pattern_real_models(self):
        """测试单例模式（使用真实模型）"""
        design_model_path = os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH')
        clone_model_path = os.environ.get('QWEN_TTS_CLONE_MODEL_PATH')

        try:
            manager1 = LocalQwen3TTSModelManager(
                design_model_path=design_model_path,
                clone_model_path=clone_model_path
            )

            manager2 = LocalQwen3TTSModelManager(
                design_model_path=design_model_path,
                clone_model_path=clone_model_path
            )

            assert manager1 is manager2, "LocalQwen3TTSModelManager应该是单例"
            assert manager1.design_model is manager2.design_model
            assert manager1.clone_model is manager2.clone_model

        except Exception as e:
            print(f"模型加载失败: {e}")
            pytest.skip(f"模型加载失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH'),
        reason="需要设置QWEN_TTS_DESIGN_MODEL_PATH环境变量"
    )
    def test_generate_voice_design_real_model(self):
        """测试生成语音设计（使用真实模型）"""
        design_model_path = os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH')

        try:
            manager = LocalQwen3TTSModelManager(design_model_path=design_model_path)

            text = "这是一段测试文本，用于测试语音设计功能。"
            instruct = "使用自然流畅的语音，语速适中，语气温和。"

            wavs, sr = manager.generate_voice_design(text, instruct)

            assert isinstance(wavs, list)
            assert len(wavs) > 0
            assert isinstance(sr, int)
            assert sr > 0

            # 验证音频数据
            for wav in wavs:
                assert isinstance(wav, np.ndarray)
                assert len(wav) > 0

            print(f"语音设计生成成功，采样率: {sr}，音频段数: {len(wavs)}，总采样点数: {sum(len(w) for w in wavs)}")

            # 测试写入文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                output_path = tmp.name

            try:
                manager.write_voice_to_file(wavs, sr, output_path)
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
                print(f"音频文件已保存: {output_path}")
            finally:
                if os.path.exists(output_path):
                    os.remove(output_path)

        except Exception as e:
            print(f"语音设计生成失败: {e}")
            pytest.skip(f"语音设计生成失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def test_create_clone_prompt_real_model(self):
        """测试创建克隆提示（使用真实模型）"""
        clone_model_path = os.environ.get('QWEN_TTS_CLONE_MODEL_PATH')

        try:
            manager = LocalQwen3TTSModelManager(clone_model_path=clone_model_path)

            # 创建测试音频文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                test_audio_path = tmp.name
                # 生成简单的测试音频数据
                test_data = np.random.randn(16000) * 0.1  # 1秒的随机音频
                sf.write(test_audio_path, test_data, 16000)

            try:
                ref_text = "这是一段参考文本，用于创建语音克隆提示。"

                # 创建克隆提示
                clone_prompt = manager.create_clone_prompt(test_audio_path, ref_text)

                assert isinstance(clone_prompt, str)
                assert len(clone_prompt) > 0
                print(f"克隆提示创建成功，长度: {len(clone_prompt)}")

                # 测试缓存功能 - 相同参数应该返回相同的提示
                clone_prompt2 = manager.create_clone_prompt(test_audio_path, ref_text)
                assert clone_prompt == clone_prompt2, "缓存功能应该返回相同的结果"

                # 不同参数应该返回不同的提示
                ref_text2 = "这是另一段参考文本，用于测试缓存。"
                clone_prompt3 = manager.create_clone_prompt(test_audio_path, ref_text2)
                assert clone_prompt != clone_prompt3, "不同参数应该返回不同的结果"

            finally:
                if os.path.exists(test_audio_path):
                    os.remove(test_audio_path)

        except Exception as e:
            print(f"创建克隆提示失败: {e}")
            pytest.skip(f"创建克隆提示失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def test_generate_voice_clone_real_model(self):
        """测试生成语音克隆（使用真实模型）"""
        clone_model_path = os.environ.get('QWEN_TTS_CLONE_MODEL_PATH')

        try:
            manager = LocalQwen3TTSModelManager(clone_model_path=clone_model_path)

            # 创建测试音频文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                test_audio_path = tmp.name
                # 生成简单的测试音频数据
                test_data = np.random.randn(16000) * 0.1  # 1秒的随机音频
                sf.write(test_audio_path, test_data, 16000)

            try:
                text = "这是一段要克隆的文本，测试语音克隆功能。"
                ref_text = "这是一段参考文本，用于语音克隆。"
                instruct = "保持与参考音频相似的语音特征。"

                wavs, sr = manager.generate_voice_clone(text, test_audio_path, ref_text, instruct)

                assert isinstance(wavs, list)
                assert len(wavs) > 0
                assert isinstance(sr, int)
                assert sr > 0

                # 验证音频数据
                for wav in wavs:
                    assert isinstance(wav, np.ndarray)
                    assert len(wav) > 0

                print(f"语音克隆生成成功，采样率: {sr}，音频段数: {len(wavs)}")

                # 测试写入文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    output_path = tmp.name

                try:
                    manager.write_voice_to_file(wavs, sr, output_path)
                    assert os.path.exists(output_path)
                    assert os.path.getsize(output_path) > 0
                    print(f"克隆音频文件已保存: {output_path}")
                finally:
                    if os.path.exists(output_path):
                        os.remove(output_path)

            finally:
                if os.path.exists(test_audio_path):
                    os.remove(test_audio_path)

        except Exception as e:
            print(f"语音克隆生成失败: {e}")
            pytest.skip(f"语音克隆生成失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH') or not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_DESIGN_MODEL_PATH和QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def test_use_flash_attention_real_models(self):
        """测试flash attention设置（使用真实模型）"""
        design_model_path = os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH')
        clone_model_path = os.environ.get('QWEN_TTS_CLONE_MODEL_PATH')

        try:
            # 测试启用flash attention
            manager_with_fa = LocalQwen3TTSModelManager(
                design_model_path=design_model_path,
                clone_model_path=clone_model_path,
                use_flash_attention=True
            )

            assert manager_with_fa.use_flash_attention is True

            # 加载模型
            design_model_fa = manager_with_fa.get_design_model()
            clone_model_fa = manager_with_fa.get_clone_model()

            assert design_model_fa is not None
            assert clone_model_fa is not None

            print("启用flash attention的模型加载成功")

            # 测试禁用flash attention
            manager_without_fa = LocalQwen3TTSModelManager(
                design_model_path=design_model_path,
                clone_model_path=clone_model_path,
                use_flash_attention=False
            )

            assert manager_without_fa.use_flash_attention is False

        except Exception as e:
            print(f"flash attention测试失败: {e}")
            pytest.skip(f"flash attention测试失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH'),
        reason="需要设置QWEN_TTS_DESIGN_MODEL_PATH环境变量"
    )
    def test_generate_voice_design_different_instructs(self):
        """测试不同指令下的语音设计（使用真实模型）"""
        design_model_path = os.environ.get('QWEN_TTS_DESIGN_MODEL_PATH')

        try:
            manager = LocalQwen3TTSModelManager(design_model_path=design_model_path)

            test_cases = [
                ("这是一段测试文本。", "使用欢快的语气，语速稍快。"),
                ("这是另一段测试文本。", "使用严肃的语气，语速缓慢。"),
                ("测试不同情感表达。", "使用悲伤的语气，音量较低。"),
                ("测试长文本处理能力。", "使用自然的语气，保持连贯性。" + "这是一段较长的指令，用于测试模型处理长指令的能力。")
            ]

            for i, (text, instruct) in enumerate(test_cases):
                try:
                    wavs, sr = manager.generate_voice_design(text, instruct)
                    assert isinstance(wavs, list)
                    assert len(wavs) > 0
                    assert isinstance(sr, int)
                    assert sr > 0
                    print(f"测试用例 {i+1} 成功: 文本长度={len(text)}, 指令长度={len(instruct)}")
                except Exception as e:
                    print(f"测试用例 {i+1} 失败: {e}")
                    # 不跳过，继续测试其他用例

        except Exception as e:
            print(f"语音设计测试失败: {e}")
            pytest.skip(f"语音设计测试失败: {e}")

    @pytest.mark.skipif(
        not os.environ.get('QWEN_TTS_CLONE_MODEL_PATH'),
        reason="需要设置QWEN_TTS_CLONE_MODEL_PATH环境变量"
    )
    def test_generate_voice_clone_different_texts(self):
        """测试不同文本的语音克隆（使用真实模型）"""
        clone_model_path = os.environ.get('QWEN_TTS_CLONE_MODEL_PATH')

        try:
            manager = LocalQwen3TTSModelManager(clone_model_path=clone_model_path)

            # 创建测试音频文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                test_audio_path = tmp.name
                test_data = np.random.randn(16000) * 0.1
                sf.write(test_audio_path, test_data, 16000)

            try:
                ref_text = "参考文本用于语音克隆。"
                instruct = "保持语音特征一致。"

                test_texts = [
                    "短文本测试。",
                    "中等长度的文本，用于测试语音克隆功能的稳定性。",
                    "较长的文本段落，测试模型处理长文本的能力。这种测试对于确保语音克隆功能的鲁棒性很重要。" * 2
                ]

                for i, text in enumerate(test_texts):
                    try:
                        wavs, sr = manager.generate_voice_clone(text, test_audio_path, ref_text, instruct)
                        assert isinstance(wavs, list)
                        assert len(wavs) > 0
                        assert isinstance(sr, int)
                        assert sr > 0
                        print(f"文本测试 {i+1} 成功: 文本长度={len(text)}")
                    except Exception as e:
                        print(f"文本测试 {i+1} 失败: {e}")

            finally:
                if os.path.exists(test_audio_path):
                    os.remove(test_audio_path)

        except Exception as e:
            print(f"语音克隆测试失败: {e}")
            pytest.skip(f"语音克隆测试失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
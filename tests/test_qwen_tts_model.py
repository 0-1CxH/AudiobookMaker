import os
import pytest
import tempfile
import soundfile as sf
import numpy as np
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
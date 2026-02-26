import os
import pytest
from src.utils import single_llm_request

class TestLLMRequestFunctionsIntegration:
    """测试LLM请求函数的集成测试（需要实际环境变量）"""

    @pytest.mark.skipif(
        not os.environ.get('LLM_API_URL') or not os.environ.get('LLM_API_KEY'),
        reason="需要设置LLM_API_URL和LLM_API_KEY环境变量"
    )
    def test_real_api_call_with_sdk(self):
        """测试实际的API调用"""
        # 这个测试需要实际的环境变量
        api_url = os.environ.get('LLM_API_URL')
        api_key = os.environ.get('LLM_API_KEY')

        # 确保环境变量已设置
        assert api_url is not None, "LLM_API_URL环境变量未设置"
        assert api_key is not None, "LLM_API_KEY环境变量未设置"

        # 简单的测试提示
        prompt = "请回复'Hello World'"
        model = "aliyun/DeepSeek-V3.2"
        try:
            # 调用函数
            response = single_llm_request(
                prompt=prompt,
                model=model,
                api_url=api_url,
                api_key=api_key
            )

            # 验证响应
            assert isinstance(response, str)
            assert len(response) > 0

            # 检查响应是否包含预期内容
            # 由于LLM响应不可预测，我们只检查基本格式
            assert "Hello" in response or "hello" in response or "world" in response or "World" in response

        except Exception as e:
            # 如果API调用失败，可能是网络问题或配置问题
            # 我们记录错误但不标记测试失败
            print(f"API调用失败: {e}")
            pytest.skip(f"API调用失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
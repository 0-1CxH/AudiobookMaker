from src.text import TaggedText
from src.utils import single_llm_request, extract_json

if __name__ == "__main__":
    tt = TaggedText.convert_from_raw_text("Hello world\n Alice: ‘Hello’, Bob: “Hi”")
    print(tt)
    print(tt.data)
    # print(single_llm_request(model="aliyun/DeepSeek-V3.2", prompt="Hello world"))
    print(extract_json("adhaoifh```json\n{\"a\": 1}\n```"))
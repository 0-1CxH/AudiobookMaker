from src.text import TextManager
from src.character import CharacterManager
from src.utils import single_llm_request, extract_json

if __name__ == "__main__":
    tt = TextManager.convert_from_raw_text("a\nb\nHello world\n Alice: ‘Hello’,\nc\nd Bob: “Hi”\ne\nf")
    cm = CharacterManager()
    # cm.extract_characters_from_raw_text("Hello world\n Alice: ‘Hello’, Bob: “Hi”")
    print(tt)
    print(tt.data)
    for i, q, c in tt.iterate_quote_and_context(3):
        print(i, q, c)
    # print(cm.characters)
    # print(single_llm_request(model="aliyun/DeepSeek-V3.2", prompt="Hello world"))
    print(extract_json("adhaoifh```json\n{\"a\": 1}\n```"))
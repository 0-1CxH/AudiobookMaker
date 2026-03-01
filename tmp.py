from src.text import TextManager
from src.character import CharacterManager
from src.voice import VoiceManager
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
    vm = VoiceManager(
        voice_lib_folder_path="./voice_lib",
        design_model_path="../models/Qwen3-TTS-VD",
        clone_model_path="../models/Qwen3-TTS-Base",
        use_flash_attention=True
    )
    vm.add_voice_design(
        voice_name="test",
        tts_instruction="音色特点：温暖柔和，语调：平稳自然，语速：适中，情感：友好亲切"
    )
    print(vm.voice_designs)
    vm.generate_reference_audio(voice_name="test")
    vm.generate_voice(voice_name="test", text="这是一个测试。", voice_save_path="./voice_lib/tmp_test.wav")
    
# ABM - 音频书制作工具

ABM（Audio Book Maker）是一个用于从文本生成有声书（音频书）的Python工具。它通过LLM自动分析文本中的人物角色、分配对话、设计语音音色，并使用TTS模型生成最终音频文件。

## 主要特性

- **自动人物提取**：使用LLM从文本中自动提取人物角色并生成角色描述
- **对话分配**：智能分析引语（对话）上下文，自动分配说话人
- **语音设计**：根据人物描述自动生成TTS语音控制指令
- **语音克隆**：基于Qwen TTS模型实现高质量的语音合成与克隆
- **项目管理**：完整的项目保存/加载机制，支持断点续执行
- **音频拼接**：自动拼接所有音频片段生成最终有声书文件

## 项目结构

```
src/
├── character.py     # 人物角色管理
├── text.py          # 文本处理与对话分析
├── voice.py         # 语音设计与TTS管理
├── workflow.py      # 主项目管理器
└── utils.py         # 工具函数（LLM请求、音频处理等）
```

运行测试
```
python -m pytest tests/ -v
```

## 核心组件

### 1. 人物角色管理 (`character.py`)

管理文本中的角色信息：
- `Character` 类：存储人物名字、描述、是否使用TTS、语音名称
- `CharacterManager` 类：管理人物列表，支持提取、添加、删除、更新操作

### 2. 文本处理 (`text.py`)

处理原始文本，提取对话和上下文：
- `TaggedTextSegment` 类：带标签的文本片段（内容+标签）
- `TextManager` 类：文本管理器，支持：
  - 按句子/行切割文本
  - 识别中英文引号提取引语
  - 为引语分配上下文（用于LLM分析）
  - 为引语分配说话人

### 3. 语音设计 (`voice.py`)

语音合成和音色设计：
- `VoiceDesign` 类：语音设计对象，包含TTS指令、参考文本、参考音频路径
- `VoiceManager` 类：管理语音设计，支持语音合成和克隆

### 4. 项目管理 (`workflow.py`)

主项目工作流管理：
- `ProjectSetting` 类：项目配置（文本切割格式、上下文窗口、模型路径等）
- `Project` 类：主项目类，包含完整的有声书制作流程

### 5. 工具函数 (`utils.py`)

实用工具函数：
- `single_llm_request()`：LLM API请求
- `extract_json()`：从LLM响应提取JSON
- `LocalQwen3TTSModelManager`：本地Qwen TTS模型管理器
- `concatenate_audio_files()`：音频文件拼接

## 工作流程

### 1. 初始化项目

```python
from src.workflow import Project

# 创建新项目
project = Project(name="my_audio_book", raw_text="文本内容...")
```

### 2. 人物提取与配置

```python
# 自动提取人物
project.extract_characters()

# 手动添加/修改人物
project.add_character(character)
project.set_character_description(name, description)
project.set_character_requires_tts(name, True)
```

### 3. 对话分配

```python
# 自动为引语分配说话人
project.generate_quote_allocation()

# 手动调整分配
project.set_quote_allocation(segment_index, speaker)
```

### 4. 语音设计

```python
# 根据人物描述生成语音设计
project.generate_voice_design()

# 生成参考音频（用于语音克隆）
project.generate_reference_audio()
```

### 5. 音频生成

```python
# 生成所有文本片段的音频
project.generate_text_to_audio_segment()

# 检查未生成的片段
not_generated = project.not_yet_generated_segments()

# 渲染最终音频文件
project.render_audio()  # 生成 final_audio.wav
```

### 6. 保存与加载

```python
# 保存项目
project.save()

# 加载已有项目
project = Project.load(name="my_audio_book")
```

## 配置环境

### 环境变量

```bash
export LLM_API_KEY="your_llm_api_key"
export LLM_API_URL="https://api.example.com/v1"
export LLM_MODEL="gpt-4"
export WORKSPACE_PATH="./workspace"  # 工作空间路径
```

### TTS模型配置

需要下载并配置Qwen TTS模型：
- 设计模型（voice design model）
- 克隆模型（voice clone model）

在项目设置中配置模型路径：
```python
project.project_setting.design_model_path = "/path/to/design_model"
project.project_setting.clone_model_path = "/path/to/clone_model"
```

## 依赖项

主要Python依赖：
- `openai` - LLM API客户端
- `torch` - 深度学习框架
- `soundfile` - 音频文件读写
- `numpy` - 数值计算
- `qwen_tts` - Qwen TTS模型

## 示例项目结构

```
workspace/
├── projects/
│   └── my_audio_book/
│       ├── project_metadata.json  # 项目元数据
│       ├── raw_text.txt           # 原始文本
│       ├── voice_artifacts/       # 音频片段
│       │   ├── segment_0.wav
│       │   ├── segment_1.wav
│       │   └── ...
│       └── final_audio.wav        # 最终音频文件
├── voice_lib/                     # 语音设计库
└── design_model/ clone_model/     # TTS模型目录
```

## 使用示例

完整的示例代码：

```python
from src.workflow import Project

# 1. 初始化项目
project = Project(name="example_book", raw_text="你的文本内容...")

# 2. 提取人物
project.extract_characters()

# 3. 设置人物TTS需求
for name in project.get_character_names():
    project.set_character_requires_tts(name, True)
    project.set_character_voice_name(name, f"voice_{name}")

# 4. 分配对话
project.generate_quote_allocation()

# 5. 生成语音设计
project.generate_voice_design()
project.generate_reference_audio()

# 6. 生成音频
project.generate_text_to_audio_segment()
project.render_audio()

# 7. 保存项目
project.save()
```

## 注意事项

1. **LLM API配置**：确保正确设置LLM API密钥和端点
2. **TTS模型**：需要下载并配置Qwen TTS模型文件
3. **内存使用**：处理大文本时注意内存使用，可调整`context_window`参数
4. **音频质量**：最终音频质量取决于TTS模型和语音设计质量
5. **错误处理**：生成过程中部分失败不会中断整体流程，可手动重新生成


## 贡献

欢迎提交问题和拉取请求！

## 待办事项

- [ ] 支持更多TTS模型
- [ ] 添加音频后处理功能（降噪、均衡等）
- [ ] 支持多语言文本处理
- [ ] 添加图形用户界面
- [ ] 优化内存使用和性能
- [ ] 添加单元测试
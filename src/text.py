import re
import concurrent.futures
from dataclasses import dataclass
from .utils import single_llm_request

@dataclass
class TaggedTextSegment:
    content: str
    tag: str

class TextManager:
    DEFAULT_TAG = "__default__"
    QUOTE_TAG = "__quote__"
    PLACEHOLDER_TAG = "__placeholder__"

    def __init__(self) -> None:
        self.data = []
        self.allocation_map = {}
    
    def __str__(self):
        return "\n".join(["[" + segment.tag + "] " + segment.content for segment in self.data])
    
    @classmethod
    def convert_from_raw_text(cls, text, split_format="line", quote_format="auto"):
        """
        将原始文本转换为一系列TaggedTextSegment

        Args:
            text: 原始文本
            split_format: 文本切割格式
                - "sentence": 按句子切割（句号、问号、感叹号等）
                - "line" or default: 按换行切割（默认）
            quote_format: 引语格式
                - "auto": 自动检测中英文引号
                - "chinese": 中文引号（"、'、「、『、（、'、"等）
                - "english": 英文引号（"、'）

        Returns:
            TextManager对象
        """
        obj = cls()

        # 根据split_format切割文本，保留切割符作为占位符
        segments = cls._split_text_by_format(text, split_format)

        # 处理每个segment
        for segment in segments:
            if not segment.strip() and segment not in ['\n', '。', '！', '？', '!', '?', '.']:
                # 跳过空segment，但保留占位符
                continue

            # 检查是否是占位符（换行符或标点符号）
            if segment in ['\n', '。', '！', '？', '!', '?', '.']:
                # 标记为占位符
                obj.data.append(TaggedTextSegment(content=segment, tag=cls.PLACEHOLDER_TAG))
                continue

            # 提取引语部分
            quote_segments = cls._extract_quotes(segment, quote_format)

            if quote_segments:
                # 有引语的情况，按引语和默认部分交替添加
                for content, is_quote in quote_segments:
                    if content.strip():
                        tag = cls.QUOTE_TAG if is_quote else cls.DEFAULT_TAG
                        obj.data.append(TaggedTextSegment(content=content, tag=tag))
            else:
                # 没有引语的情况，整个segment作为默认部分
                obj.data.append(TaggedTextSegment(content=segment, tag=cls.DEFAULT_TAG))

        return obj

    @classmethod
    def _split_text_by_format(cls, text, split_format):
        """根据split_format切割文本

        Args:
            split_format: 切割格式
                - "sentence": 按句子切割（句号、问号、感叹号等）
                - "line" or default: 按换行切割（默认）

        Returns:
            list: 切割后的文本片段，包括内容片段和占位符片段
        """

        if split_format == "sentence":
            # 按句子切割，同时保留标点符号
            # 匹配句子和句子结束符
            pattern = r'([^。！？!?.]+)([。！？!?.])?'
            matches = re.findall(pattern, text)

            result = []
            for content, punct in matches:
                if content.strip():
                    result.append(content.strip())
                if punct:
                    result.append(punct)  # 标点作为占位符
            return result
        else:  # "line" or default
            # 按换行切割，同时保留换行符作为占位符
            lines = text.split('\n')
            result = []
            for i, line in enumerate(lines):
                if line.strip():
                    result.append(line)
                # 除了最后一行，每个换行都添加占位符
                if i < len(lines) - 1:
                    result.append('\n')  # 换行符作为占位符
            return result

    @classmethod
    def _extract_quotes(cls, text, quote_format):
        """
        从文本中提取引语

        Returns:
            list of tuples: [(content, is_quote), ...]
            is_quote: True表示引语，False表示非引语
        """
        # 确定引号类型
        if quote_format == "chinese":
            open_quotes = ['"', "'", '「', '『', '（', '‘', '“']
            close_quotes = ['"', "'", '」', '』', '）', '’', '”']
        elif quote_format == "english":
            open_quotes = ['"', "'", '"', "'"]
            close_quotes = ['"', "'", '"', "'"]
        else:  # "auto"
            # 自动检测中英文引号
            open_quotes = ['"', "'", '「', '『', '（', '‘', '“', '"', "'"]
            close_quotes = ['"', "'", '」', '』', '）', '’', '”', '"', "'"]

        result = []
        current_pos = 0
        text_len = len(text)

        while current_pos < text_len:
            # 寻找下一个开引号
            next_open_pos = -1
            next_open_quote = None

            for quote in open_quotes:
                pos = text.find(quote, current_pos)
                if pos != -1 and (next_open_pos == -1 or pos < next_open_pos):
                    next_open_pos = pos
                    next_open_quote = quote

            if next_open_pos == -1:
                # 没有更多引号，添加剩余文本作为默认部分
                if current_pos < text_len:
                    remaining = text[current_pos:]
                    if remaining.strip():
                        result.append((remaining, False))
                break

            # 添加开引号之前的文本作为默认部分
            if next_open_pos > current_pos:
                default_text = text[current_pos:next_open_pos]
                if default_text.strip():
                    result.append((default_text, False))

            # 寻找对应的闭引号
            close_quote_index = open_quotes.index(next_open_quote)
            corresponding_close = close_quotes[close_quote_index]

            close_pos = text.find(corresponding_close, next_open_pos + 1)

            if close_pos == -1:
                # 引号未闭合，引语到split_format切割处结束（这里简化处理到文本结束）
                quote_text = text[next_open_pos:]
                if quote_text.strip():
                    result.append((quote_text, True))
                break
            else:
                # 引语完整
                quote_text = text[next_open_pos:close_pos + 1]
                if quote_text.strip():
                    result.append((quote_text, True))
                current_pos = close_pos + 1

        return result
    
    def iterate_quote_and_context(self, context_window: int = 10):
        """迭代所有引语及其上下文

        Args:
            context_window: 上下文窗口大小，每个引语的前后各取多少个非占位符片段

        Yields:
            tuple: (index, quote_text, context_text)
            - index: 引语在data中的索引
            - quote_text: 引语文本
            - context_text: 上下文文本（包含占位符，但context_window只计算非占位符片段）
        """
        for i, tagged_text_segment in enumerate(self.data):
            if tagged_text_segment.tag == self.QUOTE_TAG:
                # 获取前文
                pre_context_indices = []
                pre_context_count = 0
                j = i - 1

                while j >= 0 and pre_context_count < context_window:
                    if self.data[j].tag != self.PLACEHOLDER_TAG:
                        pre_context_count += 1
                    pre_context_indices.append(j)
                    j -= 1

                # 获取后文
                post_context_indices = []
                post_context_count = 0
                j = i + 1

                while j < len(self.data) and post_context_count < context_window:
                    if self.data[j].tag != self.PLACEHOLDER_TAG:
                        post_context_count += 1
                    post_context_indices.append(j)
                    j += 1

                # 构建上下文文本
                context_text = ""
                for idx in reversed(pre_context_indices):
                    context_text += self.data[idx].content

                context_text += tagged_text_segment.content

                for idx in post_context_indices:
                    context_text += self.data[idx].content

                yield i, tagged_text_segment.content, context_text
            else:
                if tagged_text_segment.tag != self.PLACEHOLDER_TAG and tagged_text_segment.tag != self.DEFAULT_TAG:
                    self.allocation_map[i] = tagged_text_segment.tag # recover allocation map
    
    def set_speaker_tag(self, segment_index, speaker_tag):
        if self.data[segment_index].tag not in [self.DEFAULT_TAG, self.PLACEHOLDER_TAG]:
            self.data[segment_index].tag = speaker_tag
            self.allocation_map[segment_index] = speaker_tag
     
    def remove_speaker_tags_by_name(self, name: str):
        for i, segment in enumerate(self.data):
            if segment.tag == name:
                self.data[i].tag = self.QUOTE_TAG

    def allocate_quote_to_character(self, character_names: set, context_window: int, max_workers: int = 10):
        """为所有引语分配说话人

        Args:
            character_names: 人物名字集合
            context_window: 上下文窗口大小
            max_workers: 最大并行工作线程数，默认为10
        """

        self.allocation_map = {}

        # 收集需要处理的所有引语任务
        tasks = []
        for segment_index, quote, context_text in self.iterate_quote_and_context(context_window):
            tasks.append((segment_index, quote, context_text))

        if not tasks:
            print("没有需要分配的引语")
            return

        print(f"开始并行处理 {len(tasks)} 个引语，使用最多 {max_workers} 个线程")

        # 定义处理单个引语的函数
        def process_quote(task):
            segment_index, quote, context_text = task

            # 构造LLM提示词，判断谁在说这句引语
            prompt = f"""请分析以下引语及其上下文，判断这句话最有可能是由哪个角色说出的。

上下文内容（包含该引语）：
{context_text}

引语内容：
"{quote}"

可选的人物角色列表：
{', '.join(sorted(character_names))}

请直接返回一个角色名字。注意：
（1）如果没有明显匹配的角色，或者上下文中并未指明说话人是谁，请返回unknown，不要强行在可选的里面选一个。
（2）如果这个引语不是一句人物说的话，而是名词列举或者修辞手法，请返回unknown。
（3）如果内容不包含引语，请返回unknown。
"""
            try:
                response = single_llm_request(prompt=prompt)
                speaker = response.strip()
                return segment_index, speaker, None
            except Exception as e:
                return segment_index, None, str(e)

        # 使用线程池并行处理
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {executor.submit(process_quote, task): task for task in tasks}

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_task):
                segment_index, speaker, error = future.result()
                task = future_to_task[future]
                _, quote, _ = task

                completed += 1
                if completed % 10 == 0 or completed == len(tasks):
                    print(f"进度：[{completed} / {len(tasks)}]，当前处理引语索引 {segment_index}")

                if error:
                    print(f"处理索引 {segment_index} 的引语时出错：{error}")
                    continue

                # 只记录有确定角色分配的情况
                if speaker in character_names:
                    self.set_speaker_tag(segment_index, speaker)
                elif speaker != "unknown":
                    print(f"警告：分配结果 '{speaker}' 不在有效人物列表中")
                else:
                    pass  # unknown 情况不记录
        


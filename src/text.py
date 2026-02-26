import re
from dataclasses import dataclass

@dataclass
class TaggedTextSegment:
    content: str
    tag: str

class TaggedText:
    DEFAULT_TAG = "__default__"
    QUOTE_TAG = "__quote__"
    PLACEHOLDER_TAG = "__placeholder__"

    def __init__(self) -> None:
        self.data = []
    
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
            TaggedText对象
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
        import re

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
        



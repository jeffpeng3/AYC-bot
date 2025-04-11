from discord import Message
from google.genai.types import (
    Part,
    Blob,
)
from core.shared import get_client
from typing import List, Tuple
import re


class MarkdownElement:
    def __init__(self, start: int, end: int, type: str):
        self.start = start
        self.end = end
        self.type = type

def find_code_blocks(text: str) -> List[Tuple[int, int]]:
    """找出所有程式碼區塊的位置"""
    pattern = r'```[\s\S]*?```'
    return [(m.start(), m.end()) for m in re.finditer(pattern, text)]


def find_inline_elements(text: str) -> List[MarkdownElement]:
    """找出所有行內 markdown 元素"""
    elements = []
    patterns = {
        'inline_code': r'`[^`]+`',
        'bold': r'\*\*[^*]+\*\*',
        'italic': r'\*[^*]+\*',
        'link': r'\[[^\]]+\]\([^)]+\)',
    }
    
    for type, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            elements.append(MarkdownElement(match.start(), match.end(), type))
    
    return sorted(elements, key=lambda x: x.start)


async def split_markdown_text(text: str, max_length: int = 2000) -> List[str]:
    """分割文本，保持 markdown 完整性"""
    if len(text) <= max_length:
        return [text]
    
    # 找出所有程式碼區塊
    code_blocks = find_code_blocks(text)
    # 找出所有行內元素
    inline_elements = find_inline_elements(text)
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        # 檢查是否在程式碼區塊中
        in_code_block = False
        next_block_start = len(text)
        
        # 找到下一個程式碼區塊
        for start, end in code_blocks:
            if start > current_pos:
                next_block_start = start
                break
            if start <= current_pos < end:
                # 如果程式碼區塊太長，需要強制分割
                block_text = text[start:end]
                if len(block_text) > max_length:
                    # 找到完整的行來分割
                    lines = block_text.split('\n')
                    current_chunk = []
                    current_length = 0
                    
                    for line in lines:
                        if current_length + len(line) + 1 > max_length - 10:  # 留些餘地給結束標記
                            # 結束當前區塊
                            chunk_text = '```python\n' + '\n'.join(current_chunk) + '\n```'
                            chunks.append(chunk_text)
                            current_chunk = []
                            current_length = 0
                        current_chunk.append(line)
                        current_length += len(line) + 1
                    
                    if current_chunk:
                        chunk_text = '```python\n' + '\n'.join(current_chunk) + '\n```'
                        chunks.append(chunk_text)
                else:
                    # 檢查是否需要先添加前綴文本
                    if current_pos < start:
                        prefix_text = text[current_pos:start].rstrip()
                        if prefix_text and len(prefix_text) >= 100:
                            chunks.append(prefix_text)
                    chunks.append(block_text)
                current_pos = end
                in_code_block = True
                break
        
        if in_code_block:
            continue
        # 計算剩餘文本長度
        remaining_length = len(text) - current_pos
        
        # 處理最後一段文本
        if chunks and remaining_length <= 1000:  # 大幅提高臨界值
            last_chunk = chunks[-1]
            # 如果最後一段不太長，嘗試與前一個片段合併
            if len(last_chunk) + remaining_length <= max_length:
                chunks[-1] = last_chunk + text[current_pos:]
                break
            
        # 如果剩餘文本小於最大長度，直接添加
        if remaining_length <= max_length:
            chunks.append(text[current_pos:])
            break
            
            
        # 計算最大可能的結束位置
        end_pos = min(current_pos + max_length, len(text))
        
        # 從後向前尋找最佳分割點
        best_pos = end_pos
        
        # 先檢查段落分隔符號
        for i in range(end_pos - 1, current_pos, -1):
            if i > 0 and text[i] == '\n' and text[i-1] == '\n':
                best_pos = i + 1  # 在段落後分割
                break
        
        # 如果沒找到段落分隔，尋找句子結束符號
        if best_pos == end_pos:
            for i in range(end_pos - 1, current_pos, -1):
                # 檢查分割點，確保不會超過限制
                max_allowed_pos = current_pos + max_length
                if text[i] in '。！？':
                    if i + 1 <= max_allowed_pos and i + 1 - current_pos >= 200:
                        best_pos = i + 1
                        break
                elif text[i] == '\n' and i > 0 and text[i-1] == '\n':
                    if i + 1 <= max_allowed_pos and i + 1 - current_pos >= 200:
                        best_pos = i + 1
                        break
                elif text[i] in '，、；':
                    if i + 1 <= max_allowed_pos and i + 1 - current_pos >= 200:
                        best_pos = i + 1
                        break

        # 如果沒有找到合適的分割點
        if best_pos == end_pos:
            remaining = len(text) - current_pos
            
            # 如果剩餘文本不多，考慮合併
            if remaining <= 1000 and chunks:
                potential_merge = chunks[-1] + text[current_pos:]
                if len(potential_merge) <= max_length:
                    chunks[-1] = potential_merge
                    break
            
            # 如果剩餘文本在限制範圍內
            if remaining <= max_length:
                best_pos = len(text)
            else:
                # 嚴格在最大長度處分割
                best_pos = current_pos + max_length
                
                # 如果找不到合適的分割點，就在限制長度處分割
                if best_pos == end_pos:
                    best_pos = current_pos + max_length
            last_chunk_size = remaining - max_length
            if last_chunk_size < 100:  # 如果最後一個片段會太小
                # 往前多取一些，確保最後一個片段夠大
                max_length = remaining - 100
            temp_pos = current_pos + max_length
            while temp_pos > current_pos + max_length - 20 and temp_pos > current_pos:
                if text[temp_pos] in '，。！？\n':
                    best_pos = temp_pos + 1
                    break
                temp_pos -= 1
            if best_pos == end_pos:  # 如果還是沒找到合適的分割點
                # 檢查最後是否會產生小片段
                if len(text) - (current_pos + max_length) < 100:
                    # 將剩餘文本合併到當前片段
                    best_pos = len(text)
                else:
                    best_pos = current_pos + max_length
                    
        # 檢查是否會切斷行內元素
        for elem in inline_elements:
            if elem.start < best_pos < elem.end:
                best_pos = elem.start
                
        chunks.append(text[current_pos:best_pos])
        current_pos = best_pos
    return chunks

async def parse_message(message: Message) -> Part:
    prefix = f'<author>{message.author.display_name}({message.author.id})</author>\n<content>'
    postfix = '</content>'
    if message.author.bot:
        prefix = ''
        postfix = ''
    part = Part(text=f'{prefix}{message.content}{postfix}')
    MIME_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }
    for file in message.attachments:
        if any([file.filename.endswith(i) for i in ["png", "jpg", "jpeg", "webp"]]):
            extension = file.filename.split(".")[-1]
            mime = MIME_type[extension]
            async with (await get_client()).get(file.url) as response:
                image_raw = await response.read()
            part.inline_data = Blob(data=image_raw, mime_type=mime)
            break
    return part

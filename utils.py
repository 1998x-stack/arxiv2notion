"""
工具函数模块
职责：提供通用工具函数
"""
import re
import sys
import json
import traceback
import unicodedata
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

import aiofiles
from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False
):
    """
    配置日志
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        verbose: 是否详细输出
    """
    # 移除默认 handler
    logger.remove()
    
    # 控制台输出
    log_level = "DEBUG" if verbose else level
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )
    
    # 文件输出
    if log_file:
        logger.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            rotation="10 MB"
        )


def format_exception() -> str:
    """
    格式化当前异常信息
    
    Returns:
        格式化的异常字符串
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_message = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
    return error_message


def clean_text(text: str) -> str:
    """
    清理文本
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 规范化 Unicode
    text = unicodedata.normalize("NFKC", text)
    
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    
    # 去除首尾空白
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def normalize_arxiv_id(arxiv_id: str) -> str:
    """
    规范化 arXiv ID
    
    支持格式:
    - 2301.08362
    - 2301.08362v1
    - arXiv:2301.08362
    - https://arxiv.org/abs/2301.08362
    - hep-th/9901001 (旧格式)
    
    Args:
        arxiv_id: 原始 ID
        
    Returns:
        规范化的 ID
    """
    if not arxiv_id:
        return ""
    
    arxiv_id = arxiv_id.strip()
    
    # 移除 arXiv: 前缀
    arxiv_id = re.sub(r'^arXiv:', '', arxiv_id, flags=re.I)
    
    # 从 URL 提取
    url_match = re.search(r'arxiv\.org/(?:abs|pdf)/([^\s/?]+)', arxiv_id)
    if url_match:
        arxiv_id = url_match.group(1)
    
    # 移除版本号（可选保留）
    # arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
    
    # 移除 .pdf 后缀
    arxiv_id = re.sub(r'\.pdf$', '', arxiv_id, flags=re.I)
    
    return arxiv_id.strip()


def extract_arxiv_ids(text: str) -> List[str]:
    """
    从文本中提取所有 arXiv ID
    
    Args:
        text: 文本内容
        
    Returns:
        arXiv ID 列表
    """
    ids = []
    
    # 新格式: YYMM.NNNNN
    new_pattern = r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b'
    ids.extend(re.findall(new_pattern, text))
    
    # 旧格式: category/YYMMNNN
    old_pattern = r'\b([a-z-]+/\d{7}(?:v\d+)?)\b'
    ids.extend(re.findall(old_pattern, text, re.I))
    
    # arXiv:ID 格式
    arxiv_pattern = r'arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)'
    ids.extend(re.findall(arxiv_pattern, text, re.I))
    
    # 去重并规范化
    normalized = []
    seen = set()
    for id_ in ids:
        norm_id = normalize_arxiv_id(id_)
        if norm_id and norm_id not in seen:
            seen.add(norm_id)
            normalized.append(norm_id)
    
    return normalized


def build_ar5iv_url(arxiv_id: str) -> str:
    """
    构建 ar5iv URL
    
    Args:
        arxiv_id: arXiv ID
        
    Returns:
        ar5iv URL
    """
    norm_id = normalize_arxiv_id(arxiv_id)
    return f"https://ar5iv.labs.arxiv.org/html/{norm_id}"


def build_arxiv_url(arxiv_id: str, type_: str = "abs") -> str:
    """
    构建 arXiv URL
    
    Args:
        arxiv_id: arXiv ID
        type_: 链接类型 (abs, pdf)
        
    Returns:
        arXiv URL
    """
    norm_id = normalize_arxiv_id(arxiv_id)
    return f"https://arxiv.org/{type_}/{norm_id}"


def build_arxiv_api_url(arxiv_id: str) -> str:
    """
    构建 arXiv API 查询 URL
    
    Args:
        arxiv_id: arXiv ID
        
    Returns:
        API URL
    """
    norm_id = normalize_arxiv_id(arxiv_id)
    return f"http://export.arxiv.org/api/query?id_list={norm_id}"


def build_arxiv_search_url(query: str, max_results: int = 5) -> str:
    """
    构建 arXiv 搜索 URL
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        
    Returns:
        API URL
    """
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    return f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results={max_results}"


async def save_json(data: Any, filepath: Path) -> bool:
    """
    异步保存 JSON 文件
    
    Args:
        data: 数据
        filepath: 文件路径
        
    Returns:
        是否成功
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        
        return True
        
    except Exception:
        error_message = format_exception()
        logger.error(f"保存 JSON 失败 {filepath}: {error_message}")
        return False


async def load_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    异步加载 JSON 文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        数据或 None
    """
    try:
        if not filepath.exists():
            return None
        
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
            
    except Exception:
        error_message = format_exception()
        logger.error(f"加载 JSON 失败 {filepath}: {error_message}")
        return None


def save_json_sync(data: Any, filepath: Path) -> bool:
    """
    同步保存 JSON 文件
    
    Args:
        data: 数据
        filepath: 文件路径
        
    Returns:
        是否成功
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return True
        
    except Exception:
        error_message = format_exception()
        logger.error(f"保存 JSON 失败 {filepath}: {error_message}")
        return False


def load_json_sync(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    同步加载 JSON 文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        数据或 None
    """
    try:
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception:
        error_message = format_exception()
        logger.error(f"加载 JSON 失败 {filepath}: {error_message}")
        return None


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单实现）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度 (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # 转小写并分词
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Jaccard 相似度
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def format_authors(authors: List[str], max_count: int = 3) -> str:
    """
    格式化作者列表
    
    Args:
        authors: 作者列表
        max_count: 最大显示数量
        
    Returns:
        格式化字符串
    """
    if not authors:
        return "Unknown Authors"
    
    if len(authors) <= max_count:
        return ", ".join(authors)
    
    return ", ".join(authors[:max_count]) + f" et al. ({len(authors)} authors)"


def format_date(dt: datetime) -> str:
    """格式化日期"""
    return dt.strftime("%Y-%m-%d")


def safe_filename(name: str) -> str:
    """
    生成安全的文件名
    
    Args:
        name: 原始名称
        
    Returns:
        安全文件名
    """
    # 移除不安全字符
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # 替换空白
    name = re.sub(r'\s+', '_', name)
    # 限制长度
    if len(name) > 100:
        name = name[:100]
    
    return name


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_category_emoji(category: str) -> str:
    """
    获取 arXiv 分类对应的 emoji
    
    Args:
        category: arXiv 分类
        
    Returns:
        emoji
    """
    category_emojis = {
        "cs.": "💻",
        "math.": "📐",
        "physics": "⚛️",
        "astro-ph": "🌟",
        "cond-mat": "🔬",
        "hep-": "⚡",
        "quant-ph": "🔮",
        "stat.": "📊",
        "econ.": "📈",
        "q-bio": "🧬",
        "q-fin": "💰",
        "eess.": "📡",
        "nlin.": "🌀",
        "nucl-": "☢️",
        "gr-qc": "🕳️",
    }
    
    category_lower = category.lower()
    for prefix, emoji in category_emojis.items():
        if category_lower.startswith(prefix):
            return emoji
    
    return "📄"
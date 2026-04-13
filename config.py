"""
配置管理模块
职责：集中管理所有配置项
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

from dotenv import load_dotenv


@dataclass
class NotionConfig:
    """Notion API 配置"""
    token: str
    root_page_id: str
    rate_limit_delay: float = 0.35
    max_retries: int = 3
    max_blocks_per_request: int = 100
    
    @classmethod
    def from_env(cls) -> "NotionConfig":
        """从环境变量加载"""
        load_dotenv()
        token = os.getenv("NOTION_TOKEN")
        root_id = os.getenv("NOTION_ROOT_PAGE_ID")
        
        if not token or not root_id:
            raise ValueError("请设置 NOTION_TOKEN 和 NOTION_ROOT_PAGE_ID 环境变量")
        
        return cls(
            token=token,
            root_page_id=root_id,
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "0.35")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            max_blocks_per_request=int(os.getenv("MAX_BLOCKS_PER_REQUEST", "100"))
        )


@dataclass
class ArxivConfig:
    """arXiv API 配置"""
    base_url: str = "http://export.arxiv.org/api/query"
    ar5iv_base_url: str = "https://ar5iv.labs.arxiv.org/html"
    request_delay: float = 3.0  # arXiv 要求最少 3 秒间隔
    max_retries: int = 3
    timeout: int = 60
    max_results_per_query: int = 10


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("./cache"))
    # Computed in __post_init__ from cache_dir — do NOT set independently
    arxiv_cache_dir: Path = field(init=False)
    ar5iv_cache_dir: Path = field(init=False)

    def __post_init__(self):
        self.arxiv_cache_dir = self.cache_dir / "arxiv"
        self.ar5iv_cache_dir = self.cache_dir / "ar5iv"
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure cache directories exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.arxiv_cache_dir.mkdir(parents=True, exist_ok=True)
        self.ar5iv_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_arxiv_cache_file(self, arxiv_id: str) -> Path:
        safe_id = arxiv_id.replace("/", "_").replace(":", "_")
        return self.arxiv_cache_dir / f"{safe_id}.json"

    def get_ar5iv_cache_file(self, arxiv_id: str) -> Path:
        safe_id = arxiv_id.replace("/", "_").replace(":", "_")
        return self.ar5iv_cache_dir / f"{safe_id}.json"


@dataclass
class ReferenceConfig:
    """参考文献处理配置"""
    resolve_arxiv_ids: bool = True  # 是否解析 arXiv ID
    search_missing_ids: bool = True  # 是否搜索未找到 ID 的论文
    max_search_results: int = 3  # 每个参考文献最多搜索结果数
    create_ref_pages: bool = True  # 是否为参考文献创建子页面
    max_ref_depth: int = 1  # 最大递归深度（1 = 只处理直接引用）
    min_title_similarity: float = 0.8  # 标题相似度阈值


@dataclass
class ContentConfig:
    """内容处理配置"""
    max_text_length: int = 2000  # Notion rich_text 限制
    include_equations: bool = True
    include_figures: bool = True
    include_tables: bool = True
    include_references: bool = True
    max_sections: int = 50  # 最大章节数
    max_figures: int = 30
    max_tables: int = 20
    max_equations: int = 100
    max_references: int = 100


@dataclass
class QwenConfig:
    """Qwen LLM annotation configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    model: str = "qwen-plus"            # DashScope model ID — verify at platform.dashscope.com
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    enabled: bool = True
    min_para_length: int = 100          # paragraphs shorter than this are skipped
    max_para_length: int = 1500         # truncate input to this before sending
    temperature: float = 0.3
    max_tokens: int = 512


@dataclass
class AppConfig:
    """应用总配置"""
    notion: NotionConfig
    arxiv: ArxivConfig = field(default_factory=ArxivConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    reference: ReferenceConfig = field(default_factory=ReferenceConfig)
    content: ContentConfig = field(default_factory=ContentConfig)
    qwen: QwenConfig = field(default_factory=QwenConfig)

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    verbose: bool = False

    # 用户代理
    user_agent: str = "ar5iv-to-notion/1.0 (Academic Research Tool)"
    
    def __post_init__(self):
        """初始化后处理"""
        self.cache.ensure_directories()
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量加载完整配置"""
        load_dotenv()
        
        return cls(
            notion=NotionConfig.from_env(),
            arxiv=ArxivConfig(
                request_delay=float(os.getenv("ARXIV_REQUEST_DELAY", "3.0"))
            ),
            cache=CacheConfig(
                enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
                cache_dir=Path(os.getenv("CACHE_DIR", "./cache"))
            ),
            reference=ReferenceConfig(
                resolve_arxiv_ids=os.getenv("RESOLVE_ARXIV_IDS", "true").lower() == "true",
                search_missing_ids=os.getenv("SEARCH_MISSING_IDS", "true").lower() == "true",
                create_ref_pages=os.getenv("CREATE_REF_PAGES", "true").lower() == "true",
                max_ref_depth=int(os.getenv("MAX_REF_DEPTH", "1"))
            ),
            qwen=QwenConfig(
                api_key=os.getenv("DASHSCOPE_API_KEY", ""),
                model=os.getenv("QWEN_MODEL", "qwen-plus"),
                enabled=os.getenv("QWEN_ENABLED", "true").lower() == "true",
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            verbose=os.getenv("VERBOSE", "false").lower() == "true"
        )


def get_test_config() -> AppConfig:
    """获取测试配置"""
    return AppConfig(
        notion=NotionConfig(
            token="test_token",
            root_page_id="test_page_id"
        )
    )
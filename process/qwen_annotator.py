"""
Qwen paragraph annotation module.
Responsibility: Call Qwen via DashScope to generate Chinese reading notes for each paragraph.
"""
import asyncio
import hashlib
import json
import re
import time
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

from loguru import logger
from tqdm.asyncio import tqdm as async_tqdm

from config import QwenConfig
from storage import FileManager
from models import Ar5ivContent, PaperData, ParagraphAnnotation
from domain.paper_document import build_paper_document, iter_paragraph_refs


SYSTEM_PROMPT = (
    "你是一位耐心的学术论文辅导老师，擅长用通俗易懂的中文解释复杂的技术段落。"
    "请保持解释简洁、准确，不超过2-3句话。"
)

USER_TEMPLATE = """你正在阅读论文《{paper_title}》。

论文摘要：
{paper_abstract}

---

现在请分析以下段落，用中文回答：

1. 通俗解读（1-2句话）：结合论文主题，用简单语言解释这段话的核心意思
2. 关键要点（2-3条）：每条一句话，提炼最重要的信息

段落原文：
{text}

回答格式（严格按此格式）：
通俗解读：...
要点1：...
要点2：...
要点3：（如有必要）"""


class QwenAnnotator:
    """
    Annotates paper paragraphs using Qwen via DashScope's OpenAI-compatible API.

    Caching: If annotations already exist on disk for a paper, the API is not called.
    """

    def __init__(self, config: QwenConfig, file_manager: FileManager):
        self.config = config
        self.fm = file_manager
        self._client = None  # lazy init

    def cache_fingerprint(self, content: Ar5ivContent, arxiv_id: str = "") -> str:
        """Invalidate annotations on source, model, prompt or config changes."""
        doc = build_paper_document(PaperData(
            arxiv_id=arxiv_id or content.paper_id, content=content,
        ))
        material = {
            "schema_version": 1,
            "content_hash": doc.content_hash,
            "model": self.config.model,
            "base_url": self.config.base_url,
            "system_prompt": SYSTEM_PROMPT,
            "user_template": USER_TEMPLATE,
            "min_para_length": self.config.min_para_length,
            "max_para_length": self.config.max_para_length,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    def _get_client(self):
        """Lazy-initialize the OpenAI client (DashScope-compatible)."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai package is required for Qwen annotation. "
                    "Run: pip install openai>=1.0.0"
                )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client

    async def _call_api(self, messages: list) -> "ChatCompletion":
        """
        Call the Qwen API (synchronous under the hood, wrapped in executor).
        Returns the raw completion response.
        """
        client = self._get_client()
        loop = asyncio.get_running_loop()

        def _sync_call():
            return client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                extra_body={"enable_thinking": False},
            )

        return await loop.run_in_executor(None, _sync_call)

    def _parse_response(self, text: str) -> Tuple[str, List[str]]:
        """
        Parse Qwen response into (plain_explanation, key_points).
        Robust to missing sections.
        """
        explanation = ""
        key_points = []

        # Extract 通俗解读
        match = re.search(r"通俗解读[：:]\s*(.+?)(?=要点\d|$)", text, re.DOTALL)
        if match:
            explanation = match.group(1).strip()

        # Extract 要点N
        for m in re.finditer(r"要点\d[：:]\s*(.+?)(?=要点\d|$)", text, re.DOTALL):
            point = m.group(1).strip()
            if point:
                key_points.append(point)

        # Fallback: if parsing fails entirely, use full response as explanation
        if not explanation:
            explanation = text.strip()[:300]

        return explanation, key_points

    async def annotate_paragraph(
        self, text: str, section_title: str, para_idx: int,
        paper_title: str = "", paper_abstract: str = "",
        node_id: str | None = None,
    ) -> ParagraphAnnotation:
        """
        Annotate a single paragraph. Returns a placeholder annotation if the
        text is shorter than config.min_para_length or if the API fails.
        """
        para_text_preview = text[:200]

        # Skip very short paragraphs
        if len(text) < self.config.min_para_length:
            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation="（段落过短，跳过注释）",
                key_points=[],
                node_id=node_id,
            )

        # Truncate long input
        truncated = text[: self.config.max_para_length]
        content = USER_TEMPLATE.format(
            paper_title=paper_title or "Unknown",
            paper_abstract=(paper_abstract[:800] + "...") if len(paper_abstract) > 800 else (paper_abstract or "N/A"),
            text=truncated,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        t0 = time.time()
        try:
            response = await self._call_api(messages)
            latency_ms = int((time.time() - t0) * 1000)
            raw = response.choices[0].message.content
            explanation, key_points = self._parse_response(raw)

            # Log the API call
            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0
            self.fm.log_llm_call({
                "section_title": section_title,
                "para_idx": para_idx,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
                "model": self.config.model,
                "cached": False,
            })

            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation=explanation,
                key_points=key_points,
                node_id=node_id,
            )

        except Exception as e:
            logger.warning(f"Qwen API failed for para {para_idx} in '{section_title}': {e}")
            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation="（注释生成失败）",
                key_points=[],
                node_id=node_id,
            )

    async def annotate_paper(
        self,
        content: Ar5ivContent,
        arxiv_id: str,
        category: str,
    ) -> List[ParagraphAnnotation]:
        """
        Annotate all paragraphs in a paper with max-concurrency=3.

        Cache-first: if annotations exist on disk, loads and returns immediately.
        Otherwise annotates concurrently (up to 3 at a time) with a tqdm bar.
        """
        fingerprint = self.cache_fingerprint(content, arxiv_id)
        if self.fm.has_annotations(arxiv_id, category, fingerprint=fingerprint):
            cached = self.fm.load_annotations(arxiv_id, category)
            logger.info(f"Loading validated annotation cache for {arxiv_id}")
            return cached

        paper_title = content.title or arxiv_id
        paper_abstract = content.abstract or ""

        logger.info(f"Annotating {arxiv_id} with Qwen ({self.config.model})...")

        # Every task references a canonical node ID; duplicate section names
        # cannot alias one another.
        tasks: List[tuple] = []
        canonical = build_paper_document(PaperData(arxiv_id=arxiv_id, content=content))

        # TL;DR from abstract
        if paper_abstract and len(paper_abstract) >= self.config.min_para_length:
            abstract_node = next(n for n in canonical.nodes if n.kind == "abstract")
            tasks.append(("__abstract__", -1, paper_abstract, abstract_node.node_id))

        # Per-section, per-paragraph, preserving canonical identities.
        for ref in iter_paragraph_refs(content):
            tasks.append((ref.section.title, ref.para_idx, ref.text, ref.node_id))

        if not tasks:
            logger.info(f"No paragraphs to annotate for {arxiv_id}")
            return []

        # Run concurrently with Semaphore(3)
        semaphore = asyncio.Semaphore(3)
        annotations: List[ParagraphAnnotation] = []

        async def _bounded_annotate(section_title: str, para_idx: int, text: str,
                                    node_id: str) -> ParagraphAnnotation:
            async with semaphore:
                return await self.annotate_paragraph(
                    text=text,
                    section_title=section_title,
                    para_idx=para_idx,
                    paper_title=paper_title,
                    paper_abstract=paper_abstract,
                    node_id=node_id,
                )

        desc = f"Annotating {arxiv_id}"
        results = await async_tqdm.gather(
            *[_bounded_annotate(s, i, t, node) for s, i, t, node in tasks],
            desc=desc,
            total=len(tasks),
        )
        annotations = list(results)

        # An API failure is not a successful cache entry. Retry on next run.
        if any(a.plain_explanation == "（注释生成失败）" for a in annotations):
            logger.warning("Incomplete LLM annotation: cache not marked valid")
        else:
            self.fm.save_annotations(arxiv_id, category, annotations,
                                     fingerprint=fingerprint)
        logger.info(f"Annotated {len(annotations)} paragraphs for {arxiv_id}")
        return annotations

    def _collect_tasks(self, section, tasks: List[tuple]) -> None:
        """Recursively collect (section_title, para_idx, text) tuples."""
        for idx, para in enumerate(section.paragraphs):
            tasks.append((section.title, idx, para))
        for sub in section.subsections:
            self._collect_tasks(sub, tasks)

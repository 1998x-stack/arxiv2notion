"""
Qwen paragraph annotation module.
Responsibility: Call Qwen via DashScope to generate Chinese reading notes for each paragraph.
"""
import asyncio
import re
import time
from typing import List, Optional, Tuple

from loguru import logger

from config import QwenConfig
from storage.file_manager import FileManager
from models import Ar5ivContent, ParagraphAnnotation


SYSTEM_PROMPT = (
    "你是一位耐心的学术论文辅导老师，擅长用通俗易懂的中文解释复杂的技术段落。"
    "请保持解释简洁、准确，不超过2-3句话。"
)

USER_TEMPLATE = """请分析以下学术段落，用中文回答：

1. 通俗解读（1-2句话）：用简单的语言解释这段话的核心意思
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

    async def _call_api(self, messages: list) -> object:
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
        self, text: str, section_title: str, para_idx: int
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
            )

        # Truncate long input
        truncated = text[: self.config.max_para_length]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(text=truncated)},
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
            )

        except Exception as e:
            logger.warning(f"Qwen API failed for para {para_idx} in '{section_title}': {e}")
            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation="（注释生成失败）",
                key_points=[],
            )

    async def annotate_paper(
        self,
        content: Ar5ivContent,
        arxiv_id: str,
        category: str,
    ) -> List[ParagraphAnnotation]:
        """
        Annotate all paragraphs in a paper.

        If annotations already exist on disk, loads and returns them without any API calls.
        Otherwise calls Qwen for each paragraph, saves to disk, and returns results.
        """
        # Cache hit — skip all API calls
        if self.fm.has_annotations(arxiv_id, category):
            logger.info(f"Loading cached annotations for {arxiv_id}")
            return self.fm.load_annotations(arxiv_id, category)

        logger.info(f"Annotating {arxiv_id} with Qwen ({self.config.model})...")
        annotations: List[ParagraphAnnotation] = []

        # Paper-level TL;DR from abstract
        if content.abstract and len(content.abstract) >= self.config.min_para_length:
            abstract_ann = await self.annotate_paragraph(
                content.abstract, section_title="__abstract__", para_idx=-1
            )
            annotations.append(abstract_ann)

        # Per-section, per-paragraph
        for section in content.sections:
            section_anns = await self._annotate_section(section)
            annotations.extend(section_anns)

        # Save to disk
        self.fm.save_annotations(arxiv_id, category, annotations)
        logger.info(f"Annotated {len(annotations)} paragraphs for {arxiv_id}")
        return annotations

    async def _annotate_section(self, section) -> List[ParagraphAnnotation]:
        """Annotate all paragraphs in a section (recursively includes subsections)."""
        annotations = []
        for idx, para in enumerate(section.paragraphs):
            ann = await self.annotate_paragraph(para, section.title, idx)
            annotations.append(ann)
        for sub in section.subsections:
            annotations.extend(await self._annotate_section(sub))
        return annotations

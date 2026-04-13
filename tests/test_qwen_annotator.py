"""Unit tests for QwenAnnotator — all Qwen API calls are mocked."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_openai_response():
    """Fake OpenAI chat completion response."""
    choice = MagicMock()
    choice.message.content = (
        "通俗解读：这段话解释了Transformer的注意力机制。\n"
        "要点1：自注意力机制允许序列内部元素相互关注。\n"
        "要点2：多头注意力扩展了单一注意力的表达能力。\n"
        "要点3：位置编码解决了无顺序信息的问题。"
    )
    response = MagicMock()
    response.choices = [choice]
    response.usage.prompt_tokens = 200
    response.usage.completion_tokens = 80
    return response


@pytest.fixture
def qwen_config():
    from config import QwenConfig
    return QwenConfig(api_key="test_key", model="qwen-plus", enabled=True, min_para_length=10)


class TestQwenAnnotatorParsing:
    def test_parse_response_extracts_explanation_and_key_points(self, qwen_config, tmp_path):
        from storage.file_manager import FileManager
        from process.qwen_annotator import QwenAnnotator
        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        raw = (
            "通俗解读：这是一个测试。\n"
            "要点1：第一点。\n"
            "要点2：第二点。\n"
        )
        explanation, points = annotator._parse_response(raw)
        assert explanation == "这是一个测试。"
        assert points == ["第一点。", "第二点。"]

    def test_parse_response_handles_missing_points_gracefully(self, qwen_config, tmp_path):
        from storage.file_manager import FileManager
        from process.qwen_annotator import QwenAnnotator
        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        raw = "通俗解读：只有解读没有要点。"
        explanation, points = annotator._parse_response(raw)
        assert "只有解读" in explanation
        assert isinstance(points, list)


class TestQwenAnnotatorAPI:
    @pytest.mark.asyncio
    async def test_annotate_paragraph_calls_api_and_returns_annotation(
        self, qwen_config, tmp_path, mock_openai_response
    ):
        from storage.file_manager import FileManager
        from process.qwen_annotator import QwenAnnotator

        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        with patch.object(annotator, "_call_api", return_value=mock_openai_response) as mock_call:
            ann = await annotator.annotate_paragraph(
                text="The dominant sequence transduction models rely on RNNs.",
                section_title="Introduction",
                para_idx=0,
            )

        mock_call.assert_called_once()
        assert ann.section_title == "Introduction"
        assert ann.para_idx == 0
        assert len(ann.plain_explanation) > 0
        assert isinstance(ann.key_points, list)

    @pytest.mark.asyncio
    async def test_annotate_paper_loads_cache_if_exists(self, qwen_config, tmp_path, sample_annotation):
        from storage.file_manager import FileManager
        from models import Ar5ivContent, Section
        from process.qwen_annotator import QwenAnnotator

        fm = FileManager(base_dir=tmp_path)
        # Pre-populate cache
        fm.save_annotations("1706.03762", "deep_learning", [sample_annotation])

        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)
        content = Ar5ivContent(
            paper_id="1706.03762",
            title="Test",
            sections=[Section(title="Introduction", level=2, paragraphs=["Some text."])],
        )

        with patch.object(annotator, "annotate_paragraph") as mock_para:
            result = await annotator.annotate_paper(content, "1706.03762", "deep_learning")

        # Must not call annotate_paragraph when cache exists
        mock_para.assert_not_called()
        assert len(result) == 1
        assert result[0].cached is True

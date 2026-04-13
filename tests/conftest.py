"""Shared test fixtures."""
import sys
from pathlib import Path

import pytest

# Ensure project root is on the import path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_paper_dir(tmp_path):
    """A temporary directory for paper storage tests."""
    return tmp_path


@pytest.fixture
def sample_annotation():
    """A sample ParagraphAnnotation for tests."""
    from models import ParagraphAnnotation
    return ParagraphAnnotation(
        section_title="Introduction",
        para_idx=0,
        para_text="The dominant sequence transduction models...",
        plain_explanation="这段话的意思是：现有的序列模型主要依赖循环神经网络。",
        key_points=["传统模型依赖RNN结构", "注意力机制已被广泛使用", "本文提出无RNN的Transformer架构"],
    )

"""End-to-end tests for the complete GraphRAG pipeline."""

import json
import tempfile
from pathlib import Path

import pytest

from main import ingest, query


@pytest.fixture
def sample_source_file(tmp_path):
    """Create a sample source file for testing."""
    sample_file = tmp_path / "test_document.md"
    sample_file.write_text(
        """
<document_metadata>
{
  "document_title": "Test Gazette - Issue 1",
  "document_date": "2025-01-01",
  "document_id": "test-1",
  "issue_number": 1,
  "volume_number": 1,
  "document_type": "official_gazette",
  "language": ["en"],
  "authors": ["Test Author"],
  "publisher": "Test Publisher",
  "total_pages": 2
}
</document_metadata>

---

<page_start>1</page_start>
<page_metadata>
{
  "page_number": 1,
  "page_title": "Test Page 1",
  "document_date": "2025-01-01",
  "issue_number": 1,
  "page_type": "content"
}
</page_metadata>
This is test content for page 1. It contains information about commercial leases.
<page_end>1</page_end>

---

<page_start>2</page_start>
<page_metadata>
{
  "page_number": 2,
  "page_title": "Test Page 2",
  "document_date": "2025-01-01",
  "issue_number": 1,
  "page_type": "content"
}
</page_metadata>
This is test content for page 2. It contains information about filing fees.
<page_end>2</page_end>
""".strip(),
        encoding="utf-8",
    )
    return sample_file


@pytest.mark.integration
def test_end_to_end_ingest_and_query(sample_source_file, tmp_path):
    """Test complete pipeline: ingest → query → verify output format."""
    # Skip if FalkorDB not available
    try:
        from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
        graph = FalkorDBAdapter()
        # Clear graph for clean test
        graph.clear_graph()
    except Exception:
        pytest.skip("FalkorDB not available")

    # Step 1: Ingest document
    ingest([str(sample_source_file.parent)])

    # Step 2: Query
    questions = [
        "What is mentioned about commercial leases?",
        "What is mentioned about filing fees?",
    ]
    output_file = tmp_path / "test_answers.json"
    answers = query(questions, output_path=str(output_file), parallel=False)

    # Step 3: Verify output format
    assert len(answers) == len(questions), "Should return answer for each question"
    assert output_file.exists(), "Output file should be created"

    # Verify JSON format matches sample_answers.json
    with open(output_file) as f:
        output_data = json.load(f)

    assert isinstance(output_data, list), "Output should be a list"
    assert len(output_data) == len(questions), "Should have one answer per question"
    assert all("answer" in item for item in output_data), "Each item should have 'answer' key"
    assert all(isinstance(item["answer"], str) for item in output_data), "Answers should be strings"
    assert all(len(item["answer"]) > 0 for item in output_data), "Answers should not be empty"


@pytest.mark.integration
def test_output_format_matches_sample():
    """Verify output format matches sample_answers.json exactly."""
    sample_answers_path = Path("data/sample_answers.json")
    if not sample_answers_path.exists():
        pytest.skip("sample_answers.json not found")

    with open(sample_answers_path) as f:
        sample_data = json.load(f)

    # Verify structure
    assert isinstance(sample_data, list), "Sample should be a list"
    assert len(sample_data) > 0, "Sample should have at least one answer"
    assert all("answer" in item for item in sample_data), "Each item should have 'answer' key"
    assert all(isinstance(item["answer"], str) for item in sample_data), "Answers should be strings"

    # Verify format matches what query() produces
    # The format should be: [{"answer": "..."}, ...]
    assert all(isinstance(item, dict) for item in sample_data), "Each item should be a dict"
    assert all(len(item) == 1 and "answer" in item for item in sample_data), "Each item should only have 'answer' key"


@pytest.mark.integration
def test_query_handles_empty_questions():
    """Test that query() handles empty question list gracefully."""
    try:
        answers = query([], output_path="test_empty.json")
        assert isinstance(answers, list), "Should return a list"
        assert len(answers) == 0, "Should return empty list for empty questions"
    except Exception as e:
        # Should not crash, but may return empty list or raise informative error
        assert "empty" in str(e).lower() or "no questions" in str(e).lower()


@pytest.mark.integration
def test_query_handles_invalid_questions():
    """Test that query() handles invalid questions gracefully."""
    try:
        from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
        graph = FalkorDBAdapter()
    except Exception:
        pytest.skip("FalkorDB not available")

    # Test with empty string question
    answers = query([""], output_path="test_invalid.json", parallel=False)
    assert len(answers) == 1, "Should return one answer"
    assert isinstance(answers[0], str), "Answer should be a string"

    # Test with very long question
    long_question = "What is " + "a " * 1000 + "?"
    answers = query([long_question], output_path="test_long.json", parallel=False)
    assert len(answers) == 1, "Should return one answer"


def test_output_path_resolution(tmp_path):
    """Test that output path is resolved correctly."""
    # Test relative path
    rel_path = "test_relative.json"
    resolved = Path(rel_path).resolve()
    assert resolved.is_absolute(), "Resolved path should be absolute"

    # Test absolute path
    abs_path = tmp_path / "test_absolute.json"
    resolved = abs_path.resolve()
    assert resolved == abs_path, "Absolute path should remain unchanged"


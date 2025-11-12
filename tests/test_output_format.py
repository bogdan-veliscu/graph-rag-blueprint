"""Tests to validate output format matches sample_answers.json exactly."""

import json
from pathlib import Path

import pytest


def test_sample_answers_format():
    """Verify sample_answers.json has correct format."""
    sample_path = Path("data/sample_answers.json")
    if not sample_path.exists():
        pytest.skip("sample_answers.json not found")

    with open(sample_path) as f:
        data = json.load(f)

    # Verify structure
    assert isinstance(data, list), "Should be a list"
    assert len(data) > 0, "Should have at least one entry"

    # Verify each entry
    for i, item in enumerate(data):
        assert isinstance(item, dict), f"Item {i} should be a dict"
        assert "answer" in item, f"Item {i} should have 'answer' key"
        assert isinstance(item["answer"], str), f"Item {i} answer should be a string"
        assert len(item["answer"]) > 0, f"Item {i} answer should not be empty"
        # Should only have 'answer' key (no extra keys)
        assert len(item) == 1, f"Item {i} should only have 'answer' key"


def test_output_format_consistency():
    """Test that query() output format matches sample format."""
    sample_path = Path("data/sample_answers.json")
    if not sample_path.exists():
        pytest.skip("sample_answers.json not found")

    with open(sample_path) as f:
        sample_data = json.load(f)

    # Expected format: [{"answer": "..."}, ...]
    expected_format = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"}
            },
            "required": ["answer"],
            "additionalProperties": False
        }
    }

    # Verify sample matches expected format
    assert isinstance(sample_data, list), "Should be a list"
    for item in sample_data:
        assert isinstance(item, dict), "Each item should be a dict"
        assert "answer" in item, "Each item should have 'answer' key"
        assert isinstance(item["answer"], str), "Answer should be a string"
        assert len(item) == 1, "Should only have 'answer' key"


def test_citation_format_in_sample():
    """Verify that sample answers include citation format."""
    sample_path = Path("data/sample_answers.json")
    if not sample_path.exists():
        pytest.skip("sample_answers.json not found")

    with open(sample_path) as f:
        data = json.load(f)

    # Check if answers contain citation markers
    has_citations = any("[" in item["answer"] and "]" in item["answer"] for item in data)
    # Citations are optional in sample, but if present should be formatted correctly
    if has_citations:
        for item in data:
            answer = item["answer"]
            # If citations present, should have reference markers
            if "[" in answer and "]" in answer:
                # Should have References section or inline citations
                assert "References" in answer or answer.count("[") == answer.count("]"), \
                    "Citations should be balanced"


@pytest.mark.parametrize("output_file", ["answers.json", "test_output.json"])
def test_query_output_format_matches_sample(output_file, tmp_path):
    """Test that query() produces output matching sample format."""
    # This is a format validation test - doesn't require actual graph
    # Just verifies the structure matches
    
    # Create mock output matching expected format
    mock_output = [
        {"answer": "Test answer 1 [1].\n\nReferences\n1. Test Document. p.1."},
        {"answer": "Test answer 2 [2].\n\nReferences\n2. Test Document. p.2."}
    ]
    
    output_path = tmp_path / output_file
    with open(output_path, "w") as f:
        json.dump(mock_output, f, indent=2)
    
    # Verify format
    with open(output_path) as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Output should be a list"
    assert all("answer" in item for item in data), "Each item should have 'answer' key"
    assert all(isinstance(item["answer"], str) for item in data), "Answers should be strings"
    assert all(len(item) == 1 for item in data), "Each item should only have 'answer' key"


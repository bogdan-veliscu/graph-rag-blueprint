"""Source data parser for legal documents with XML tags."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from graph_rag.models import DocumentMetadata, PageMetadata, ParsedSourceDocument
from graph_rag.utils.text_utils import parse_orig_tags

logger = logging.getLogger(__name__)


def _parse_json_with_orig_tags(json_str: str, page_number: int) -> Dict[str, Any]:
    """Parse JSON that may contain <orig> tags breaking the structure.
    
    Strategy:
    1. Try normal JSON parsing first
    2. If that fails, try to fix by escaping <orig> tags temporarily
    3. If that fails, try to extract key-value pairs using regex
    4. Fall back to empty dict
    
    Args:
        json_str: JSON string that may contain <orig> tags
        page_number: Page number for logging
        
    Returns:
        Parsed metadata dictionary
    """
    # Try 1: Normal JSON parsing
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Try 2: Escape <orig> tags temporarily, parse, then restore
    try:
        # Replace <orig>...</orig> with a placeholder that won't break JSON
        orig_pattern = re.compile(r'<orig>(.*?)</orig>', re.DOTALL)
        placeholders = {}
        placeholder_counter = [0]
        
        def replace_orig(match):
            placeholder = f"__ORIG_PLACEHOLDER_{placeholder_counter[0]}__"
            placeholders[placeholder] = match.group(1)
            placeholder_counter[0] += 1
            return f'"{placeholder}"'  # Wrap in quotes so it's valid JSON string
        
        fixed_json = orig_pattern.sub(replace_orig, json_str)
        metadata_dict = json.loads(fixed_json)
        
        # Restore <orig> tags in string values
        for key, value in metadata_dict.items():
            if isinstance(value, str):
                for placeholder, orig_content in placeholders.items():
                    value = value.replace(placeholder, f"<orig>{orig_content}</orig>")
                metadata_dict[key] = value
        
        return metadata_dict
    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"Failed to fix JSON with placeholders on page {page_number}: {e}")
    
    # Try 3: Extract key-value pairs using regex (lenient parsing)
    try:
        metadata_dict = {}
        # Match "key": "value" or "key": value patterns
        key_value_pattern = re.compile(r'"([^"]+)":\s*("([^"]*)"|(\d+)|(true|false|null))', re.DOTALL)
        
        for match in key_value_pattern.finditer(json_str):
            key = match.group(1)
            # Check which capture group matched
            if match.group(3):  # String value
                value = match.group(3)
                # Parse <orig> tags in the value
                value_display, value_orig = parse_orig_tags(value)
                metadata_dict[key] = value_display
                if value_orig:
                    metadata_dict[f"{key}_original"] = value_orig
            elif match.group(4):  # Number
                metadata_dict[key] = int(match.group(4))
            elif match.group(5):  # Boolean or null
                if match.group(5) == "true":
                    metadata_dict[key] = True
                elif match.group(5) == "false":
                    metadata_dict[key] = False
                else:  # null
                    metadata_dict[key] = None
        
        if metadata_dict:
            logger.debug(f"Extracted {len(metadata_dict)} fields using regex on page {page_number}")
            return metadata_dict
    except Exception as e:
        logger.debug(f"Failed regex extraction on page {page_number}: {e}")
    
    # Fallback: log warning and return empty dict
    logger.warning(
        f"Failed to parse page_metadata JSON on page {page_number}. "
        f"Using empty metadata. JSON was: {json_str[:200]}"
    )
    return {}


def parse_source_data(file_path: Path) -> ParsedSourceDocument:
    """Parse a source data markdown file with XML tags.

    Args:
        file_path: Path to the markdown file

    Returns:
        ParsedSourceDocument with document metadata and pages
    """
    content = file_path.read_text(encoding="utf-8")

    # Extract document metadata
    document_metadata = _parse_document_metadata(content)

    # Extract pages
    pages = _parse_page_content(content, document_metadata)

    return ParsedSourceDocument(
        document_metadata=document_metadata,
        pages=pages,
    )


def _parse_document_metadata(content: str) -> DocumentMetadata:
    """Extract document-level metadata from content.

    Supports both JSON format: <document_metadata>{...}</document_metadata>
    and key-value format: <document_metadata>key: value...</document_metadata>

    Args:
        content: Full file content

    Returns:
        DocumentMetadata object
    """
    # Find document_metadata tag
    match = re.search(r"<document_metadata>\s*(.*?)\s*</document_metadata>", content, re.DOTALL)
    if not match:
        raise ValueError("No <document_metadata> tag found")

    metadata_content = match.group(1).strip()
    metadata_dict = {}

    # Try JSON format first
    if metadata_content.startswith("{"):
        try:
            metadata_dict = json.loads(metadata_content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse document_metadata as JSON, trying key-value format")
            metadata_dict = {}
    
    # If not JSON or JSON failed, try key-value format
    if not metadata_dict:
        for line in metadata_content.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # Handle special cases
            if key == "language":
                # Can be single value or list
                metadata_dict[key] = [v.strip() for v in value.split(",")] if "," in value else [value]
            elif key == "total_pages":
                try:
                    metadata_dict[key] = int(value)
                except ValueError:
                    metadata_dict[key] = None
            elif key == "issue_number" or key == "volume_number":
                try:
                    metadata_dict[key] = int(value) if value else None
                except ValueError:
                    metadata_dict[key] = None
            elif key == "authors":
                # Handle list format if present
                if value.startswith("[") and value.endswith("]"):
                    try:
                        metadata_dict[key] = json.loads(value)
                    except json.JSONDecodeError:
                        metadata_dict[key] = [value] if value else []
                else:
                    metadata_dict[key] = [value] if value else []
            else:
                metadata_dict[key] = value if value else None
        
        # Set defaults for missing fields
        if "document_title" not in metadata_dict:
            metadata_dict["document_title"] = metadata_dict.get("document_id", "")
        if "language" not in metadata_dict:
            metadata_dict["language"] = []

    # Parse <orig> tags in title and publisher
    title = metadata_dict.get("document_title", "")
    title_display, title_orig = parse_orig_tags(title)
    if title_orig:
        metadata_dict["document_title_original"] = title_orig
        metadata_dict["document_title"] = title_display

    publisher = metadata_dict.get("publisher")
    if publisher:
        pub_display, pub_orig = parse_orig_tags(publisher)
        if pub_orig:
            metadata_dict["publisher_original"] = pub_orig
            metadata_dict["publisher"] = pub_display

    # Parse authors with <orig> tags
    authors_raw = metadata_dict.get("authors", [])
    # Handle authors field: can be string, list of strings, or None
    if authors_raw is None:
        authors_list = []
    elif isinstance(authors_raw, str):
        # Single author string - convert to list
        authors_list = [authors_raw]
    elif isinstance(authors_raw, list):
        # Already a list
        authors_list = authors_raw
    else:
        # Fallback: convert to string and wrap in list
        authors_list = [str(authors_raw)]
    
    parsed_authors = []
    for author in authors_list:
        if isinstance(author, str):
            auth_display, auth_orig = parse_orig_tags(author)
            parsed_authors.append(auth_display)
            if auth_orig:
                # Store original names separately if needed
                pass

    return DocumentMetadata(
        document_title=metadata_dict.get("document_title", ""),
        document_date=metadata_dict.get("document_date", ""),
        document_id=metadata_dict.get("document_id", ""),
        issue_number=metadata_dict.get("issue_number"),
        volume_number=metadata_dict.get("volume_number"),
        document_type=metadata_dict.get("document_type"),
        language=metadata_dict.get("language", []),
        authors=parsed_authors,
        publisher=metadata_dict.get("publisher"),
        document_summary=metadata_dict.get("document_summary"),
        total_pages=metadata_dict.get("total_pages"),
        processed=metadata_dict.get("processed"),
    )


def _parse_page_content(
    content: str, document_metadata: DocumentMetadata
) -> List[Dict[str, Any]]:
    """Extract page content and metadata.

    Args:
        content: Full file content
        document_metadata: Document metadata for inheritance

    Returns:
        List of page dictionaries with metadata and content
    """
    pages = []
    page_pattern = re.compile(
        r"<page_start>(\d+)</page_start>(.*?)<page_end>\1</page_end>", re.DOTALL
    )

    for match in page_pattern.finditer(content):
        page_number = int(match.group(1))
        page_content = match.group(2)

        # Extract page metadata
        page_metadata = _parse_page_metadata(
            page_content, page_number, document_metadata
        )

        # Extract page body content (excluding metadata tags)
        page_body = _extract_page_body(page_content)

        pages.append(
            {
                "page_number": page_number,
                "metadata": page_metadata,
                "content": page_body,
            }
        )

    return pages


def _parse_page_metadata(
    page_content: str, page_number: int, document_metadata: DocumentMetadata
) -> PageMetadata:
    """Extract page-level metadata.

    Args:
        page_content: Content between page_start and page_end tags
        page_number: Page number
        document_metadata: Document metadata for inheritance

    Returns:
        PageMetadata object
    """
    # Find page_metadata tag
    metadata_match = re.search(
        r"<page_metadata>\s*(\{.*?\})\s*</page_metadata>", page_content, re.DOTALL
    )

    if metadata_match:
        metadata_json = metadata_match.group(1)
        metadata_dict = _parse_json_with_orig_tags(metadata_json, page_number)
    else:
        metadata_dict = {}

    # Inherit from document metadata if not present
    document_date = metadata_dict.get("document_date") or document_metadata.document_date
    issue_number = metadata_dict.get("issue_number") or document_metadata.issue_number
    volume_number = (
        metadata_dict.get("volume_number") or document_metadata.volume_number
    )
    document_type = (
        metadata_dict.get("document_type") or document_metadata.document_type
    )

    # Fix date inheritance bug: if date is "1954-12-11" (gazette founding date),
    # use document date instead
    if document_date == "1954-12-11" and document_metadata.document_date:
        document_date = document_metadata.document_date

    # Parse <orig> tags in publisher
    publisher = metadata_dict.get("publisher")
    if publisher:
        pub_display, pub_orig = parse_orig_tags(publisher)
        if pub_orig:
            metadata_dict["publisher_original"] = pub_orig
            metadata_dict["publisher"] = pub_display

    # Extract header and footer
    header_match = re.search(r"<header>(.*?)</header>", page_content, re.DOTALL)
    footer_match = re.search(r"<footer>(.*?)</footer>", page_content, re.DOTALL)

    header = header_match.group(1).strip() if header_match else None
    footer = footer_match.group(1).strip() if footer_match else None

    return PageMetadata(
        page_number=page_number,
        page_title=metadata_dict.get("page_title"),
        document_date=document_date,
        issue_number=issue_number,
        volume_number=volume_number,
        document_type=document_type,
        languages_detected=metadata_dict.get("languages_detected", []),
        page_type=metadata_dict.get("page_type"),
        authors=metadata_dict.get("authors"),
        publisher=metadata_dict.get("publisher"),
        page_summary=metadata_dict.get("page_summary"),
        header=header,
        footer=footer,
    )


def _extract_page_body(page_content: str) -> str:
    """Extract page body content, excluding metadata tags.

    Args:
        page_content: Content between page_start and page_end tags

    Returns:
        Clean page body text
    """
    # Remove metadata tags
    body = re.sub(r"<page_metadata>.*?</page_metadata>", "", page_content, flags=re.DOTALL)
    body = re.sub(r"<header>.*?</header>", "", body, flags=re.DOTALL)
    body = re.sub(r"<footer>.*?</footer>", "", body, flags=re.DOTALL)

    # Extract table captions and tables for metadata
    table_captions = re.findall(r"<table_caption>(.*?)</table_caption>", body, re.DOTALL)
    tables = re.findall(r"<table>(.*?)</table>", body, re.DOTALL)

    # Remove table tags but keep content
    body = re.sub(r"<table_caption>", "", body)
    body = re.sub(r"</table_caption>", "", body)
    body = re.sub(r"<table>", "", body)
    body = re.sub(r"</table>", "", body)

    # Extract <orig> spans for metadata
    orig_spans = re.findall(r"<orig>(.*?)</orig>", body)

    return body.strip()


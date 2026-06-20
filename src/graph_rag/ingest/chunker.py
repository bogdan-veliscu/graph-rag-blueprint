"""Document chunking utilities."""

import re
from typing import List

import tiktoken

from graph_rag.config import config
from graph_rag.models import Chunk, Page


def chunk_document_pages(document_id: str, pages: List[Page]) -> List[Chunk]:
    """Chunk document pages into semantic chunks.

    Args:
        document_id: Document ID
        pages: List of Page objects

    Returns:
        List of Chunk objects
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    chunks = []

    for page in pages:
        page_chunks = _chunk_page(page, document_id, encoding)
        chunks.extend(page_chunks)

    return chunks


def _chunk_page(page: Page, document_id: str, encoding: tiktoken.Encoding) -> List[Chunk]:
    """Chunk a single page into semantic chunks.

    Args:
        page: Page object
        document_id: Document ID
        encoding: Tiktoken encoding

    Returns:
        List of Chunk objects for this page
    """
    text = page.content
    tokens = encoding.encode(text)
    chunks = []

    # Extract table captions and tables for metadata
    table_captions = re.findall(r"<table_caption>(.*?)</table_caption>", text, re.DOTALL)
    tables = re.findall(r"<table>(.*?)</table>", text, re.DOTALL)
    orig_spans = re.findall(r"<orig>(.*?)</orig>", text)

    start_idx = 0
    chunk_index = 0

    while start_idx < len(tokens):
        # Calculate chunk boundaries
        end_idx = min(start_idx + config.chunk_size, len(tokens))
        chunk_tokens = tokens[start_idx:end_idx]

        # Decode tokens back to text
        chunk_text = encoding.decode(chunk_tokens)

        # Calculate character positions (approximate)
        text_before = encoding.decode(tokens[:start_idx])
        start_char = len(text_before)
        end_char = start_char + len(chunk_text)

        # Create chunk ID
        chunk_id = f"{page.id}_chunk_{chunk_index}"

        chunk = Chunk(
            id=chunk_id,
            document_id=document_id,
            page_id=page.id,
            page_number=page.page_number,
            text=chunk_text,
            metadata={
                "table_captions": table_captions,
                "tables": tables,
                "orig_spans": orig_spans,
            },
            source_file=document_id,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
        )
        chunks.append(chunk)

        # Move start index with overlap
        start_idx += config.chunk_size - config.chunk_overlap
        chunk_index += 1

    return chunks


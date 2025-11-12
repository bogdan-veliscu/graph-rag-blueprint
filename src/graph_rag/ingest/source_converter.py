"""Convert parsed source documents to Document/Page models."""

from datetime import datetime
from typing import List

from src.graph_rag.models import Document, Page, ParsedSourceDocument


def convert_source_to_document_nodes(
    parsed: ParsedSourceDocument,
) -> tuple[Document, List[Page]]:
    """Convert parsed source document to Document and Page models.

    Args:
        parsed: ParsedSourceDocument from parser

    Returns:
        Tuple of (Document, List[Page])
    """
    doc_metadata = parsed.document_metadata

    # Create Document model
    document = Document(
        id=doc_metadata.document_id,
        filename=doc_metadata.document_id,
        title=doc_metadata.document_title,
        doc_type=doc_metadata.document_type,
        metadata={
            "document_date": doc_metadata.document_date,
            "issue_number": doc_metadata.issue_number,
            "volume_number": doc_metadata.volume_number,
            "language": doc_metadata.language,
            "authors": doc_metadata.authors,
            "publisher": doc_metadata.publisher,
            "document_summary": doc_metadata.document_summary,
            "total_pages": doc_metadata.total_pages,
            "processed": doc_metadata.processed,
        },
        created_at=datetime.now(),
    )

    # Create Page models
    pages = []
    for page_data in parsed.pages:
        page_metadata = page_data["metadata"]
        page = Page(
            id=f"{doc_metadata.document_id}_page_{page_metadata.page_number}",
            document_id=doc_metadata.document_id,
            page_number=page_metadata.page_number,
            content=page_data["content"],
            metadata={
                "page_title": page_metadata.page_title,
                "document_date": page_metadata.document_date,
                "issue_number": page_metadata.issue_number,
                "volume_number": page_metadata.volume_number,
                "document_type": page_metadata.document_type,
                "languages_detected": page_metadata.languages_detected,
                "page_type": page_metadata.page_type,
                "authors": page_metadata.authors,
                "publisher": page_metadata.publisher,
                "page_summary": page_metadata.page_summary,
                "header": page_metadata.header,
                "footer": page_metadata.footer,
            },
            created_at=datetime.now(),
        )
        pages.append(page)

    return document, pages


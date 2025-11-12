"""Core data models for the GraphRAG system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """Graph node types."""

    DOCUMENT = "Document"
    PAGE = "Page"
    CHUNK = "Chunk"
    ENTITY = "Entity"


class EdgeType(str, Enum):
    """Graph edge types."""

    PART_OF = "PART_OF"
    DOCUMENT_HAS_PAGE = "DOCUMENT_HAS_PAGE"
    PAGE_HAS_CHUNK = "PAGE_HAS_CHUNK"
    MENTIONS = "MENTIONS"
    RELATED_TO = "RELATED_TO"
    DOCUMENT_PUBLISHED_BY = "DOCUMENT_PUBLISHED_BY"
    PAGE_AUTHORED_BY = "PAGE_AUTHORED_BY"


class EntityType(str, Enum):
    """Entity types for extraction."""

    PARTY = "PARTY"
    DATE = "DATE"
    AMOUNT = "AMOUNT"
    CLAUSE_REF = "CLAUSE_REF"
    LEGAL_TERM = "LEGAL_TERM"
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"


@dataclass
class DocumentMetadata:
    """Document-level metadata."""

    document_title: str
    document_date: str
    document_id: str
    issue_number: Optional[int] = None
    volume_number: Optional[int] = None
    document_type: Optional[str] = None
    language: List[str] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    publisher: Optional[str] = None
    document_summary: Optional[str] = None
    total_pages: Optional[int] = None
    processed: Optional[str] = None


@dataclass
class PageMetadata:
    """Page-level metadata."""

    page_number: int
    page_title: Optional[str] = None
    document_date: Optional[str] = None
    issue_number: Optional[int] = None
    volume_number: Optional[int] = None
    document_type: Optional[str] = None
    languages_detected: List[str] = field(default_factory=list)
    page_type: Optional[str] = None
    authors: Optional[List[str]] = None
    publisher: Optional[str] = None
    page_summary: Optional[str] = None
    header: Optional[str] = None
    footer: Optional[str] = None


@dataclass
class Document:
    """Document model."""

    id: str
    filename: str
    title: str
    doc_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class Page:
    """Page model."""

    id: str
    document_id: str
    page_number: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class Chunk:
    """Chunk model."""

    id: str
    document_id: str
    page_id: str
    page_number: int
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0


@dataclass
class Entity:
    """Entity model."""

    id: str
    text: str
    entity_type: EntityType
    canonical_form: Optional[str] = None
    original_name: Optional[str] = None  # For <orig> tag parsing
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Relationship model."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedSourceDocument:
    """Parsed source document structure."""

    document_metadata: DocumentMetadata
    pages: List[Dict[str, Any]]  # List of page dicts with metadata and content


@dataclass
class ChunkMatch:
    """Chunk match from retrieval."""

    chunk_id: str
    score: float
    chunk: Optional[Chunk] = None
    semantic_score: float = 0.0
    graph_score: float = 0.0


@dataclass
class AnswerResult:
    """Answer generation result."""

    answer: str
    citations: List[str]
    chunk_ids: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    explainability: Optional[Dict[str, Any]] = None  # Explainability information


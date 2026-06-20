"""Graph builder for constructing knowledge graph."""

from typing import Dict, List

from sentence_transformers import SentenceTransformer

from graph_rag.config import config
from graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from graph_rag.models import (
    Chunk,
    Document,
    EdgeType,
    Entity,
    NodeType,
    Page,
    Relationship,
)


class GraphBuilder:
    """Builds knowledge graph from documents, pages, chunks, and entities."""

    def __init__(self, graph_adapter: FalkorDBAdapter):
        """Initialize graph builder.

        Args:
            graph_adapter: FalkorDB adapter instance
        """
        self.graph = graph_adapter
        self.embedding_model = SentenceTransformer(config.embedding_model)

    def add_document_node(self, document: Document) -> None:
        """Add document node to graph.

        Args:
            document: Document object
        """
        # Use document_title from metadata if available
        title = document.metadata.get("document_title", document.title)

        properties = {
            "id": document.id,
            "filename": document.filename,
            "title": title,
            "doc_type": document.doc_type or "",
            "document_date": document.metadata.get("document_date", ""),
            "issue_number": document.metadata.get("issue_number"),
            "volume_number": document.metadata.get("volume_number"),
            "publisher": document.metadata.get("publisher", ""),
        }
        # Add all metadata fields
        for key, value in document.metadata.items():
            if key not in properties:
                properties[key] = value

        self.graph.create_node(NodeType.DOCUMENT, document.id, properties)

    def add_page_node(self, page: Page) -> None:
        """Add page node to graph.

        Args:
            page: Page object
        """
        properties = {
            "id": page.id,
            "document_id": page.document_id,
            "page_number": page.page_number,
            "content": page.content,
            "page_title": page.metadata.get("page_title", ""),
            "publisher": page.metadata.get("publisher", ""),
            "authors": page.metadata.get("authors"),
        }
        # Add all metadata fields
        for key, value in page.metadata.items():
            if key not in properties:
                properties[key] = value

        self.graph.create_node(NodeType.PAGE, page.id, properties)

        # Create document-page edge
        self.graph.create_edge(
            page.document_id,
            page.id,
            EdgeType.DOCUMENT_HAS_PAGE.value,
            NodeType.DOCUMENT,
            NodeType.PAGE,
        )

    def add_chunk_node(self, chunk: Chunk) -> None:
        """Add chunk node to graph.

        Args:
            chunk: Chunk object
        """
        # Generate embedding if not present
        if chunk.embedding is None:
            chunk.embedding = self.embedding_model.encode(
                chunk.text, show_progress_bar=False
            ).tolist()

        properties = {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "page_id": chunk.page_id,
            "page_number": chunk.page_number,
            "text": chunk.text,
            "source_file": chunk.source_file or chunk.document_id,
            "chunk_index": chunk.chunk_index,
        }
        # Add metadata
        for key, value in chunk.metadata.items():
            properties[key] = value

        self.graph.create_node(NodeType.CHUNK, chunk.id, properties)

        # Create page-chunk edge
        self.graph.create_edge(
            chunk.page_id,
            chunk.id,
            EdgeType.PAGE_HAS_CHUNK.value,
            NodeType.PAGE,
            NodeType.CHUNK,
        )

        # Create document-chunk edge (PART_OF)
        self.graph.create_edge(
            chunk.id,
            chunk.document_id,
            EdgeType.PART_OF.value,
            NodeType.CHUNK,
            NodeType.DOCUMENT,
        )

    def add_entity_node(self, entity: Entity) -> None:
        """Add entity node to graph.

        Args:
            entity: Entity object
        """
        properties = {
            "id": entity.id,
            "text": entity.text,
            "entity_type": entity.entity_type.value,
            "canonical_form": entity.canonical_form or entity.text,
        }
        if entity.original_name:
            properties["original_name"] = entity.original_name

        # Add metadata
        for key, value in entity.metadata.items():
            properties[key] = value

        self.graph.create_node(NodeType.ENTITY, entity.id, properties)

    def add_mentions_edge(self, chunk_id: str, entity_id: str) -> None:
        """Add MENTIONS edge between chunk and entity.

        Args:
            chunk_id: Chunk ID
            entity_id: Entity ID
        """
        self.graph.create_edge(
            chunk_id,
            entity_id,
            EdgeType.MENTIONS.value,
            NodeType.CHUNK,
            NodeType.ENTITY,
        )

    def add_mentions_edges_batch(
        self, edges: List[tuple[str, str]], batch_size: int = 1000
    ) -> None:
        """Add multiple MENTIONS edges in batch.

        Args:
            edges: List of (chunk_id, entity_id) tuples
            batch_size: Number of edges per batch
        """
        edge_dicts = [
            {
                "source_id": chunk_id,
                "target_id": entity_id,
                "edge_type": EdgeType.MENTIONS.value,
                "source_type": NodeType.CHUNK,
                "target_type": NodeType.ENTITY,
                "properties": None,
            }
            for chunk_id, entity_id in edges
        ]
        self.graph.create_edges_batch(edge_dicts, batch_size=batch_size)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add relationship edge.

        Args:
            relationship: Relationship object
        """
        self.graph.create_edge(
            relationship.source_id,
            relationship.target_id,
            relationship.edge_type.value,
            NodeType.ENTITY,
            NodeType.ENTITY,
            properties={"weight": relationship.weight, **relationship.metadata},
        )

    def add_relationships_batch(
        self, relationships: List[Relationship], batch_size: int = 1000
    ) -> None:
        """Add multiple relationship edges in batch.

        Args:
            relationships: List of Relationship objects
            batch_size: Number of edges per batch
        """
        edge_dicts = [
            {
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "edge_type": rel.edge_type.value,
                "source_type": NodeType.ENTITY,
                "target_type": NodeType.ENTITY,
                "properties": {"weight": rel.weight, **rel.metadata},
            }
            for rel in relationships
        ]
        self.graph.create_edges_batch(edge_dicts, batch_size=batch_size)

    def add_publisher_edge(self, document_id: str, publisher_entity_id: str) -> None:
        """Add DOCUMENT_PUBLISHED_BY edge.

        Args:
            document_id: Document ID
            publisher_entity_id: Publisher entity ID
        """
        self.graph.create_edge(
            document_id,
            publisher_entity_id,
            EdgeType.DOCUMENT_PUBLISHED_BY.value,
            NodeType.DOCUMENT,
            NodeType.ENTITY,
        )

    def add_author_edge(self, page_id: str, author_entity_id: str) -> None:
        """Add PAGE_AUTHORED_BY edge.

        Args:
            page_id: Page ID
            author_entity_id: Author entity ID
        """
        self.graph.create_edge(
            page_id,
            author_entity_id,
            EdgeType.PAGE_AUTHORED_BY.value,
            NodeType.PAGE,
            NodeType.ENTITY,
        )


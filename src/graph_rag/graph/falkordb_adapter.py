"""FalkorDB adapter for graph operations."""

from typing import Any, Dict, List, Optional

import redis
from redis.commands.graph import Graph

from src.graph_rag.config import config
from src.graph_rag.models import Document, Entity, NodeType, Page


class FalkorDBAdapter:
    """Adapter for FalkorDB graph operations."""

    def __init__(self):
        """Initialize FalkorDB connection."""
        self.redis_client = redis.Redis(
            host=config.falkordb_host,
            port=config.falkordb_port,
            decode_responses=True,
        )
        self.graph = Graph(self.redis_client, config.falkordb_graph_name)

    def create_node(
        self,
        node_type: NodeType,
        node_id: str,
        properties: Dict[str, Any],
    ) -> None:
        """Create a graph node.

        Args:
            node_type: Type of node
            node_id: Node ID
            properties: Node properties
        """
        # Filter out None values and convert properties to strings for FalkorDB
        props_list = [f"id: '{node_id}'"]
        for k, v in properties.items():
            if k != "id" and v is not None:  # Skip None values and id (already added)
                props_list.append(f"{k}: {self._format_property(v)}")
        props_str = ", ".join(props_list)
        query = f"CREATE (:{node_type.value} {{{props_str}}})"
        self.graph.query(query)

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        source_type: NodeType,
        target_type: NodeType,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a graph edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Edge type label
            source_type: Source node type
            target_type: Target node type
            properties: Optional edge properties
        """
        props_str = ""
        if properties:
            # Filter out None values
            filtered_props = {k: v for k, v in properties.items() if v is not None}
            if filtered_props:
                props_list = [f"{k}: {self._format_property(v)}" for k, v in filtered_props.items()]
                props_str = " {" + ", ".join(props_list) + "}"

        query = f"""
        MATCH (a:{source_type.value} {{id: '{source_id}'}})
        MATCH (b:{target_type.value} {{id: '{target_id}'}})
        CREATE (a)-[:{edge_type}{props_str}]->(b)
        """
        self.graph.query(query)

    def create_edges_batch(
        self,
        edges: List[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> None:
        """Create multiple edges in batches for better performance.

        Args:
            edges: List of edge dictionaries with keys:
                - source_id: Source node ID
                - target_id: Target node ID
                - edge_type: Edge type label
                - source_type: Source node type (NodeType enum)
                - target_type: Target node type (NodeType enum)
                - properties: Optional edge properties dict
            batch_size: Number of edges to create per batch
        """
        if not edges:
            return

        # Process in batches
        for batch_start in range(0, len(edges), batch_size):
            batch = edges[batch_start : batch_start + batch_size]
            
            # Build UNWIND query for batch creation
            # Format: UNWIND $edges AS edge MATCH ... CREATE ...
            edge_data = []
            for edge in batch:
                source_id = edge["source_id"].replace("'", "\\'")
                target_id = edge["target_id"].replace("'", "\\'")
                edge_type = edge["edge_type"]
                source_type = edge["source_type"].value if hasattr(edge["source_type"], "value") else edge["source_type"]
                target_type = edge["target_type"].value if hasattr(edge["target_type"], "value") else edge["target_type"]
                
                props_str = ""
                if edge.get("properties"):
                    filtered_props = {k: v for k, v in edge["properties"].items() if v is not None}
                    if filtered_props:
                        props_list = [f"{k}: {self._format_property(v)}" for k, v in filtered_props.items()]
                        props_str = " {" + ", ".join(props_list) + "}"
                
                edge_data.append({
                    "source_id": source_id,
                    "target_id": target_id,
                    "edge_type": edge_type,
                    "source_type": source_type,
                    "target_type": target_type,
                    "props_str": props_str,
                })
            
            # Build batch query - need WITH clause between MATCH-CREATE pairs
            # Format: MATCH ... MATCH ... CREATE ... WITH ... MATCH ... MATCH ... CREATE ...
            query_parts = []
            for i, edge in enumerate(edge_data):
                query_parts.append(f"MATCH (a{i}:{edge['source_type']} {{id: '{edge['source_id']}'}})")
                query_parts.append(f"MATCH (b{i}:{edge['target_type']} {{id: '{edge['target_id']}'}})")
                query_parts.append(f"CREATE (a{i})-[:{edge['edge_type']}{edge['props_str']}]->(b{i})")
                # Add WITH clause between updates (except for last one)
                if i < len(edge_data) - 1:
                    query_parts.append(f"WITH a{i}, b{i}")
            
            combined_query = "\n".join(query_parts)
            self.graph.query(combined_query)

    def get_node(self, node_type: NodeType, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID.

        Args:
            node_type: Type of node
            node_id: Node ID

        Returns:
            Node properties dict or None if not found
        """
        query = f"MATCH (n:{node_type.value} {{id: '{node_id}'}}) RETURN n"
        result = self.graph.query(query)
        if result.result_set:
            node = result.result_set[0][0]
            # Handle Node object from FalkorDB
            if hasattr(node, 'properties'):
                return dict(node.properties)
            # Fallback for dict-like objects
            elif isinstance(node, dict):
                return dict(node)
            else:
                # Try to convert to dict
                return dict(node)
        return None

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document node.

        Args:
            document_id: Document ID

        Returns:
            Document object or None
        """
        node_data = self.get_node(NodeType.DOCUMENT, document_id)
        if not node_data:
            return None

        return Document(
            id=node_data.get("id", document_id),
            filename=node_data.get("filename", ""),
            title=node_data.get("title", ""),
            doc_type=node_data.get("doc_type"),
            metadata=node_data,
        )

    def get_page(self, page_id: str) -> Optional[Page]:
        """Get a page node.

        Args:
            page_id: Page ID

        Returns:
            Page object or None
        """
        node_data = self.get_node(NodeType.PAGE, page_id)
        if not node_data:
            return None

        return Page(
            id=node_data.get("id", page_id),
            document_id=node_data.get("document_id", ""),
            page_number=node_data.get("page_number", 0),
            content=node_data.get("content", ""),
            metadata=node_data,
        )

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get a chunk node.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk properties dict or None
        """
        return self.get_node(NodeType.CHUNK, chunk_id)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query.

        Args:
            query: Cypher query string

        Returns:
            List of result dictionaries with column names as keys
        """
        result = self.graph.query(query)
        results = []
        
        # Extract column names from headers
        # Headers format: [[column_index, column_name], ...]
        column_names = []
        if result.header:
            for header_row in result.header:
                if len(header_row) >= 2:
                    column_names.append(header_row[1])  # column_name is at index 1
        
        # If no column names found, use default
        if not column_names:
            column_names = ["value"]
        
        # Map rows to dictionaries using column names
        for row in result.result_set:
            if isinstance(row[0], dict):
                # Already a dict (node/edge properties)
                results.append(dict(row[0]))
            elif len(row) == len(column_names):
                # Map each value to its column name
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(column_names):
                        row_dict[column_names[i]] = value
                results.append(row_dict)
            else:
                # Fallback: single value
                results.append({column_names[0] if column_names else "value": row[0]})
        
        return results

    def _format_property(self, value: Any) -> str:
        """Format a property value for Cypher query.

        Args:
            value: Property value

        Returns:
            Formatted string
        """
        if value is None:
            return "null"
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "\\'")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, list):
            # Format list as Cypher array: [value1, value2, ...]
            formatted_items = []
            for item in value:
                if isinstance(item, str):
                    escaped = item.replace("'", "\\'")
                    formatted_items.append(f"'{escaped}'")
                elif isinstance(item, (int, float, bool)):
                    formatted_items.append(str(item).lower() if isinstance(item, bool) else str(item))
                elif isinstance(item, (list, dict)):
                    import json
                    formatted_items.append(json.dumps(item))
                else:
                    escaped = str(item).replace("'", "\\'")
                    formatted_items.append(f"'{escaped}'")
            return "[" + ", ".join(formatted_items) + "]"
        elif isinstance(value, dict):
            import json
            return json.dumps(value)
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            # Fallback: convert to string and escape
            escaped = str(value).replace("'", "\\'")
            return f"'{escaped}'"


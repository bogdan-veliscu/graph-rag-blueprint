"""Configuration settings for the GraphRAG system."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load .env file from project root (where main.py is located)
# This ensures .env is found regardless of where Python is invoked from
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
load_dotenv(dotenv_path=env_file, override=False)  # override=False: env vars take precedence


@dataclass
class Config:
    """System configuration."""

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 128

    # Retrieval
    dense_top_k: int = 50
    sparse_top_k: int = 50
    fusion_k: int = 60  # RRF parameter

    # Graph Traversal
    max_hops: int = 2
    ppr_alpha: float = 0.15  # PageRank damping factor

    # Reranking
    rerank_top_k: int = 10

    # Generation
    llm_temperature: float = 0.1
    llm_max_tokens: int = 512

    # Parallelization
    max_concurrent: int = int(os.getenv("MAX_CONCURRENT", "128"))
    query_batch_size: int = int(os.getenv("QUERY_BATCH_SIZE", "10"))
    ingestion_workers: int = int(os.getenv("INGESTION_WORKERS", "0"))  # 0 = auto (CPU count, max 8)

    # Entity Resolution
    entity_similarity_threshold: float = 0.85

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # LLM Provider
    llm_provider: Literal["ollama", "anthropic"] = os.getenv(
        "LLM_PROVIDER", "ollama"
    ).lower()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_base_url: str = os.getenv(
        "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages"
    )

    # FalkorDB
    falkordb_host: str = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", "6379"))
    falkordb_graph_name: str = os.getenv("FALKORDB_GRAPH_NAME", "legal_graph")

    # Output directories
    output_dir: Path = Path("output")
    embeddings_file: Path = Path("output/embeddings.npy")
    bm25_file: Path = Path("output/bm25.pkl")
    chunks_file: Path = Path("output/chunks.json")

    def __post_init__(self):
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()


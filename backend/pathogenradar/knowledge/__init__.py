"""Knowledge-graph package. Use :func:`get_knowledge_graph` to obtain the configured repo."""

from __future__ import annotations

from functools import lru_cache

from .networkx_repo import NetworkXGraphRepo
from .repo import DiseaseMatch, EpiParams, KnowledgeGraphRepo

__all__ = [
    "DiseaseMatch",
    "EpiParams",
    "KnowledgeGraphRepo",
    "NetworkXGraphRepo",
    "get_knowledge_graph",
]


@lru_cache(maxsize=1)
def get_knowledge_graph() -> KnowledgeGraphRepo:
    """Return the configured knowledge graph implementation.

    Today this is the NetworkX implementation. To swap in Neo4j, return a Neo4jGraphRepo
    here — no application code changes required.
    """
    return NetworkXGraphRepo()

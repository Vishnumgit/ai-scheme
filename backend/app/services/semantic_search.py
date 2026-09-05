"""
Semantic Search & Hybrid Retrieval Service for Government Schemes.
Uses pgvector cosine distance when embeddings are present,
with automatic fallback to keyword/full-text matching.
"""
import logging
import os
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.schemas.scheme import SchemeResponse
from app.repositories.scheme_repository import SchemeRepository
from app.ingestion.embedder import generate_embedding, EMBEDDING_PROVIDER

logger = logging.getLogger(__name__)


class SemanticSearchService:

    @classmethod
    async def embed_query(cls, query_text: str) -> Tuple[Optional[List[float]], int, str]:
        """Generate embedding for search query."""
        return await generate_embedding(query_text)

    @classmethod
    async def search(
        cls,
        session: AsyncSession,
        query_text: str,
        limit: int = 20
    ) -> List[SchemeResponse]:
        """
        Execute semantic search against scheme_embeddings table if available,
        otherwise fall back to ILIKE text search.
        """
        if not query_text or not query_text.strip():
            schemes, _ = await SchemeRepository.list_schemes(session, limit=limit)
            return schemes

        # Attempt embedding generation
        vector, dim, model_name = await cls.embed_query(query_text)

        if vector and dim > 0:
            col = "embedding_768" if dim == 768 else "embedding_1536"
            # Format vector as pgvector string e.g. '[0.123, 0.456, ...]'
            vec_str = "[" + ",".join(str(x) for x in vector) + "]"

            sql = text(f"""
                SELECT s.id
                FROM schemes s
                JOIN scheme_embeddings se ON s.id = se.scheme_id
                WHERE se.{col} IS NOT NULL
                  AND s.status = 'active'
                ORDER BY se.{col} <=> cast(:vector as vector) ASC
                LIMIT :limit;
            """)
            try:
                res = await session.execute(sql, {"vector": vec_str, "limit": limit})
                scheme_ids = [row[0] for row in res.fetchall()]
                if scheme_ids:
                    results = []
                    for sid in scheme_ids:
                        scheme_resp = await SchemeRepository.get_by_id(session, sid)
                        if scheme_resp:
                            results.append(scheme_resp)
                    return results
            except Exception as e:
                logger.warning("Vector search query failed (%s), falling back to keyword search", e)

        # Fallback to keyword matching in repository
        schemes, _ = await SchemeRepository.list_schemes(session, query=query_text, limit=limit)
        return schemes

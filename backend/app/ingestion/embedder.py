"""
Embedder — generates vector embeddings for scheme records using
the configured embedding provider (Gemini or OpenAI).

Rules:
  1. Embeddings are generated AFTER normalization and validation.
  2. Only generate for quality score >= threshold.
  3. Cache: skip re-embedding if content hash unchanged.
  4. Embedding text is stored alongside the vector for auditability.
  5. Both 768-dim (Gemini) and 1536-dim (OpenAI) columns are supported.
"""
import logging
import os
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "gemini")  # gemini | openai | none
EMBEDDING_MODEL_GEMINI = os.environ.get("EMBEDDING_MODEL", "text-embedding-004")
EMBEDDING_MODEL_OPENAI = os.environ.get("EMBEDDING_MODEL_OPENAI", "text-embedding-3-small")
MIN_QUALITY_FOR_EMBEDDING = int(os.environ.get("MIN_EMBEDDING_QUALITY", "40"))


def build_embedding_text(scheme: dict) -> str:
    """
    Construct the text to embed.
    Combines key fields for maximum semantic coverage.
    Field order is intentional — name + ministry first for high-weight terms.
    """
    parts = []

    if scheme.get("name"):
        parts.append(f"Scheme: {scheme['name']}")
    if scheme.get("short_name") and scheme["short_name"] != scheme.get("name"):
        parts.append(f"Also known as: {scheme['short_name']}")
    if scheme.get("ministry"):
        parts.append(f"Ministry: {scheme['ministry']}")
    if scheme.get("department"):
        parts.append(f"Department: {scheme['department']}")
    if scheme.get("description"):
        parts.append(f"Description: {scheme['description'][:500]}")
    if scheme.get("beneficiary_types"):
        parts.append(f"Beneficiaries: {', '.join(scheme['beneficiary_types'])}")
    if scheme.get("gender_eligibility") and "Any" not in scheme["gender_eligibility"]:
        parts.append(f"Target gender: {', '.join(scheme['gender_eligibility'])}")
    if scheme.get("social_categories"):
        parts.append(f"Social categories: {', '.join(scheme['social_categories'])}")
    if scheme.get("business_types"):
        parts.append(f"Business types: {', '.join(scheme['business_types'])}")
    if scheme.get("eligibility_text"):
        parts.append(f"Eligibility: {scheme['eligibility_text'][:400]}")
    if scheme.get("benefits_text"):
        parts.append(f"Benefits: {scheme['benefits_text'][:300]}")
    if scheme.get("states"):
        parts.append(f"States: {', '.join(scheme['states'][:5])}")
    if scheme.get("government_level"):
        parts.append(f"Government level: {scheme['government_level']}")
    if scheme.get("funding_type"):
        parts.append(f"Funding type: {scheme['funding_type']}")
    if scheme.get("udyam_required"):
        parts.append("Udyam registration required")
    if scheme.get("startup_requirements"):
        parts.append("Startup focused scheme")
    if scheme.get("farmer_requirements"):
        parts.append("Farmer / agricultural scheme")
    if scheme.get("artisan_requirements"):
        parts.append("Artisan / handicraft scheme")

    return "\n".join(parts)


async def generate_embedding(text: str) -> Tuple[Optional[List[float]], int, str]:
    """
    Generate embedding for the given text using the configured provider.

    Returns:
        (embedding_vector, dimension, model_name)
        Returns (None, 0, "") on failure.
    """
    if EMBEDDING_PROVIDER == "gemini":
        return await _embed_gemini(text)
    elif EMBEDDING_PROVIDER == "openai":
        return await _embed_openai(text)
    else:
        logger.info("Embedding provider is 'none' — skipping embedding generation")
        return None, 0, ""


async def _embed_gemini(text: str) -> Tuple[Optional[List[float]], int, str]:
    """Generate embedding using Google Gemini text-embedding-004 (768-dim)."""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — skipping embedding")
            return None, 0, ""

        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model=f"models/{EMBEDDING_MODEL_GEMINI}",
            content=text,
            task_type="retrieval_document",
        )
        embedding = result["embedding"]
        return embedding, len(embedding), EMBEDDING_MODEL_GEMINI
    except Exception as e:
        logger.error("Gemini embedding failed: %s", e)
        return None, 0, ""


async def _embed_openai(text: str) -> Tuple[Optional[List[float]], int, str]:
    """Generate embedding using OpenAI text-embedding-3-small (1536-dim)."""
    try:
        from openai import AsyncOpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set — skipping embedding")
            return None, 0, ""

        client = AsyncOpenAI(api_key=api_key)
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL_OPENAI,
            input=text[:8192],  # model token limit
        )
        embedding = response.data[0].embedding
        return embedding, len(embedding), EMBEDDING_MODEL_OPENAI
    except Exception as e:
        logger.error("OpenAI embedding failed: %s", e)
        return None, 0, ""

"""
AI Service — Generates personalized explanations and document guidance
using LLM providers (Google Gemini or OpenRouter) with deterministic fallback.

Guiding principle:
AI is strictly an explanatory and guidance assistant.
All factual scheme criteria and rules come deterministically from the database.
"""
import logging
import os
from typing import List, Optional
from abc import ABC, abstractmethod

from app.schemas.user import EntrepreneurProfileBase
from app.schemas.scheme import SchemeResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    @abstractmethod
    async def explain_match(
        self,
        profile: EntrepreneurProfileBase,
        scheme: SchemeResponse,
        match_factors: List[str]
    ) -> str:
        pass


class GeminiProvider(BaseAIProvider):
    """Google Gemini LLM explanation provider."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._configured = False
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self._configured = True
            except Exception as e:
                logger.warning("Failed to configure Google Generative AI: %s", e)

    async def explain_match(
        self,
        profile: EntrepreneurProfileBase,
        scheme: SchemeResponse,
        match_factors: List[str]
    ) -> str:
        if not self._configured:
            return _generate_deterministic_explanation(profile, scheme, match_factors)

        prompt = (
            f"Explain in 2-3 clear, encouraging sentences why the government scheme '{scheme.title}' "
            f"administered by {scheme.ministry_or_org} is relevant to an entrepreneur named {profile.full_name or 'the applicant'}. "
            f"Key matching factors: {', '.join(match_factors) if match_factors else 'General eligibility'}. "
            f"Highlight specific benefits like subsidy or credit support clearly without technical jargon."
        )

        try:
            response = await self.model.generate_content_async(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning("Gemini AI explanation failed (%s), using fallback", e)

        return _generate_deterministic_explanation(profile, scheme, match_factors)


def _generate_deterministic_explanation(
    profile: EntrepreneurProfileBase,
    scheme: SchemeResponse,
    match_factors: List[str]
) -> str:
    """High-quality deterministic fallback explanation."""
    name = profile.full_name or "your profile"
    if not match_factors:
        return (
            f"You are eligible to apply for {scheme.title} under {scheme.ministry_or_org}. "
            f"This program provides structured financial or operational assistance for micro and small enterprises."
        )

    summary = "; ".join(match_factors[:3])
    subsidy_text = ""
    if scheme.subsidy_percentage and scheme.subsidy_percentage > 0:
        subsidy_text = f" and offers up to {scheme.subsidy_percentage}% government capital subsidy"

    return (
        f"Strong match for {name} based on verified criteria: {summary}. "
        f"This scheme is actively supported by {scheme.ministry_or_org}{subsidy_text}."
    )


class AIService:
    _instance: Optional['AIService'] = None

    def __init__(self):
        self.provider_type = getattr(settings, "AI_PROVIDER", "gemini").lower()
        self.enabled = getattr(settings, "AI_EXPLANATION_ENABLED", False)
        gemini_key = getattr(settings, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

        if self.provider_type == "gemini" and gemini_key:
            self.provider: Optional[BaseAIProvider] = GeminiProvider(api_key=gemini_key)
        else:
            self.provider = None

    @classmethod
    def get_instance(cls) -> 'AIService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def explain(
        self,
        profile: EntrepreneurProfileBase,
        scheme: SchemeResponse,
        match_factors: List[str]
    ) -> str:
        if self.enabled and self.provider:
            return await self.provider.explain_match(profile, scheme, match_factors)
        return _generate_deterministic_explanation(profile, scheme, match_factors)

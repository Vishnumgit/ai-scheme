"""
Backward-compatibility adapter for AISchemeRecommender.
Delegates to RecommendationService.
"""
import asyncio
from typing import List
from app.schemas.user import EntrepreneurProfileBase
from app.schemas.scheme import SchemeResponse, SchemeMatchResult
from app.services.recommendation_service import RecommendationService


class AISchemeRecommender:
    """Legacy alias wrapping RecommendationService."""

    @classmethod
    def recommend(
        cls,
        user: EntrepreneurProfileBase,
        schemes: List[SchemeResponse]
    ) -> List[SchemeMatchResult]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If inside an existing event loop, run via future or create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, RecommendationService.recommend(user, schemes)).result()
            else:
                return asyncio.run(RecommendationService.recommend(user, schemes))
        except Exception:
            # Synchronous deterministic fallback
            from app.services.matching_engine import RuleBasedMatchingEngine
            results = []
            for s in schemes:
                eval_res = RuleBasedMatchingEngine.evaluate_eligibility(user, s)
                if not eval_res.get("passed", True):
                    continue
                results.append(
                    SchemeMatchResult(
                        scheme=s,
                        match_score=eval_res["score"],
                        eligibility_status=eval_res["status"],
                        ai_reasoning=f"Matched for {user.full_name or 'profile'} based on {', '.join(eval_res['match_factors'][:2])}",
                        key_benefits=RecommendationService._extract_benefits(s),
                        required_documents=RecommendationService._generate_document_checklist(user, s),
                        score_breakdown=eval_res.get("score_breakdown"),
                        matching_factors=eval_res["match_factors"]
                    )
                )
            results.sort(key=lambda x: x.match_score, reverse=True)
            return results

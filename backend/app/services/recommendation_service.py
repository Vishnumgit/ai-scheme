"""
Recommendation Service — combines deterministic rule evaluation,
rich benefit synthesis, dynamic document checklist compilation, and explainable AI.
"""
from typing import List
from app.schemas.user import EntrepreneurProfileBase
from app.schemas.scheme import SchemeResponse, SchemeMatchResult
from app.services.matching_engine import RuleBasedMatchingEngine
from app.services.ai_service import AIService


class RecommendationService:

    @classmethod
    async def recommend(
        cls,
        user: EntrepreneurProfileBase,
        schemes: List[SchemeResponse]
    ) -> List[SchemeMatchResult]:
        results = []
        ai_service = AIService.get_instance()

        for scheme in schemes:
            eval_result = RuleBasedMatchingEngine.evaluate_eligibility(user, scheme)
            factors = eval_result["match_factors"]
            missing = eval_result["missing_requirements"]

            # If disqualified by hard rules, skip or keep only if eligible
            if not eval_result.get("passed", True):
                continue

            reasoning = await ai_service.explain(user, scheme, factors)
            benefits = cls._extract_benefits(scheme)
            docs = cls._generate_document_checklist(user, scheme)

            results.append(
                SchemeMatchResult(
                    scheme=scheme,
                    match_score=eval_result["score"],
                    eligibility_status=eval_result["status"],
                    ai_reasoning=reasoning,
                    key_benefits=benefits,
                    required_documents=docs,
                    score_breakdown=eval_result.get("score_breakdown"),
                    missing_requirements=missing,
                    matching_factors=factors
                )
            )

        # Sort highest match score first
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

    @staticmethod
    def _extract_benefits(scheme: SchemeResponse) -> List[str]:
        benefits = []
        # First check structured benefits if present
        if scheme.benefits:
            for b in scheme.benefits:
                desc = b.description or f"{b.benefit_type} support"
                if b.percentage:
                    desc += f" up to {b.percentage}%"
                elif b.amount:
                    desc += f" up to ₹{b.amount:,.0f}"
                benefits.append(desc)

        # Fallback / augment with top-level attributes
        if not benefits:
            if scheme.subsidy_percentage and scheme.subsidy_percentage > 0:
                benefits.append(f"Government Capital Subsidy up to {scheme.subsidy_percentage}%")
            if scheme.max_funding_amount and scheme.max_funding_amount > 0:
                benefits.append(f"Financial assistance / loan limit up to ₹{scheme.max_funding_amount:,.0f}")
            benefits.append("Institutional credit support & collateral-free access")

        return benefits[:4]

    @staticmethod
    def _generate_document_checklist(user: EntrepreneurProfileBase, scheme: SchemeResponse) -> List[str]:
        docs = []

        # Use structured documents from database if present
        if scheme.documents:
            for d in scheme.documents:
                name = d.document_name
                if d.mandatory:
                    name += " (Mandatory)"
                docs.append(name)

        # Ensure base essentials
        base_docs = [
            "Aadhaar Card / Government Photo ID",
            "Bank Account Details (Passbook / Cancelled Cheque)",
            "Detailed Project Report / Business Proposal"
        ]
        for b in base_docs:
            if not any(b.split()[0].lower() in d.lower() for d in docs):
                docs.append(b)

        if user.social_category and user.social_category.upper() in ["SC", "ST", "OBC"]:
            cert = f"Caste / Community Certificate ({user.social_category})"
            if not any("caste" in d.lower() or "community" in d.lower() for d in docs):
                docs.append(cert)

        if user.is_differently_abled:
            if not any("disability" in d.lower() or "udid" in d.lower() for d in docs):
                docs.append("Disability Certificate / UDID Card")

        if scheme.udyam_required:
            if not user.is_udyam_registered:
                docs.append("Udyam Registration Certificate (Free online via udyamregistration.gov.in)")
            else:
                docs.append("Udyam Registration Certificate")

        return docs

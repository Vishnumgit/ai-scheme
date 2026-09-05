"""
Rule-Based Matching Engine for Schemes.
Wraps EligibilityEvaluator to provide comprehensive compatibility and clear scoring.
"""
from typing import Dict, Any, List
from app.schemas.user import EntrepreneurProfileBase
from app.schemas.scheme import SchemeResponse
from app.services.eligibility_evaluator import EligibilityEvaluator


class RuleBasedMatchingEngine:
    """
    Evaluates hard constraints and weights demographic criteria
    specifically prioritizing marginalized entrepreneurs:
    - Women entrepreneurs
    - SC / ST / OBC / Minorities
    - Differently-abled individuals
    - Micro & small artisan/craft enterprises
    """

    @staticmethod
    def evaluate_eligibility(user: EntrepreneurProfileBase, scheme: SchemeResponse) -> Dict[str, Any]:
        passed, positive_factors, failure_reasons = EligibilityEvaluator.evaluate_hard_rules(user, scheme)

        if not passed:
            return {
                "score": 0.0,
                "status": "Ineligible",
                "match_factors": [],
                "missing_requirements": failure_reasons,
                "score_breakdown": None,
                "passed": False
            }

        score, breakdown, soft_factors = EligibilityEvaluator.score_soft_rules(user, scheme, hard_passed=True)
        all_factors = list(dict.fromkeys(positive_factors + soft_factors))

        if score >= 80:
            status = "Highly Eligible"
        elif score >= 60:
            status = "Eligible"
        else:
            status = "Partially Eligible"

        return {
            "score": score,
            "status": status,
            "match_factors": all_factors,
            "missing_requirements": [],
            "score_breakdown": breakdown,
            "passed": True
        }

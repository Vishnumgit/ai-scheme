"""
Eligibility Evaluator — deterministic engine for evaluating
hard constraints and scoring soft match criteria for entrepreneurs.

Rules:
1. Hard constraints strictly filter out non-qualifying schemes (prevent hallucinated eligibility).
2. Soft criteria provide weighted scoring across demographics, business sector, and affirmative priorities.
3. Every score factor is auditable and returned with transparent reasoning.
"""
from typing import List, Tuple, Dict, Any, Optional
from app.schemas.user import EntrepreneurProfileBase
from app.schemas.scheme import SchemeResponse, ScoreBreakdown


class EligibilityEvaluator:

    @staticmethod
    def evaluate_hard_rules(
        profile: EntrepreneurProfileBase,
        scheme: SchemeResponse
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Evaluate hard disqualifying rules.
        Returns:
            (passed: bool, positive_factors: List[str], failure_reasons: List[str])
        """
        positive_factors = []
        failure_reasons = []

        # 1. State / Geography Check
        if scheme.states and len(scheme.states) > 0 and scheme.government_level != "central":
            if profile.state:
                scheme_states_lower = [s.lower() for s in scheme.states]
                if profile.state.lower() not in scheme_states_lower:
                    failure_reasons.append(f"Restricted to states: {', '.join(scheme.states)}")

        # 2. Gender Restriction Check
        if scheme.gender_eligibility and len(scheme.gender_eligibility) > 0:
            gender_opts = [g.lower() for g in scheme.gender_eligibility]
            if "any" not in gender_opts:
                if profile.gender:
                    if profile.gender.lower() not in gender_opts:
                        failure_reasons.append(f"Designated for {', '.join(scheme.gender_eligibility)} entrepreneurs only")
                    else:
                        positive_factors.append(f"Direct match for gender criterion ({profile.gender})")

        # 3. Social Category Exclusivity
        if scheme.social_categories and len(scheme.social_categories) > 0:
            target_cats = [c.lower() for c in scheme.social_categories]
            # If General or Any is included, everyone qualifies
            if not any(c in ["any", "general", "all"] for c in target_cats):
                if profile.social_category:
                    if profile.social_category.lower() not in target_cats:
                        # Check if scheme is exclusively for specific communities
                        if all(c in ["sc", "st"] for c in target_cats) and profile.social_category.lower() not in ["sc", "st"]:
                            failure_reasons.append(f"Dedicated exclusively to {', '.join(scheme.social_categories)} communities")
                        elif target_cats and profile.social_category.lower() not in target_cats:
                            # Soft penalty or exclusion depending on target
                            pass
                    else:
                        positive_factors.append(f"Affirmative target community: {profile.social_category}")

        # 4. Differently Abled Specificity
        if scheme.disability_eligibility and not profile.is_differently_abled:
            # If scheme's sole beneficiary is PwD
            if scheme.beneficiary_types and all("pwd" in b.lower() or "disab" in b.lower() for b in scheme.beneficiary_types):
                failure_reasons.append("Dedicated program for differently-abled persons")

        passed = len(failure_reasons) == 0
        return passed, positive_factors, failure_reasons

    @staticmethod
    def score_soft_rules(
        profile: EntrepreneurProfileBase,
        scheme: SchemeResponse,
        hard_passed: bool
    ) -> Tuple[float, ScoreBreakdown, List[str]]:
        """
        Calculate weighted soft match score and detailed breakdown.
        """
        if not hard_passed:
            return 0.0, ScoreBreakdown(hard_filter_passed=False), []

        demographic_score = 0.0
        business_score = 0.0
        category_score = 0.0
        matching_factors = []

        # 1. Demographic Scoring (up to 35 pts)
        if profile.gender and profile.gender.lower() == "female":
            g_elig = [g.lower() for g in (scheme.gender_eligibility or scheme.target_demographics)]
            if any(term in g_elig for term in ["female", "women", "woman"]):
                demographic_score += 25.0
                matching_factors.append("High priority reservation for Women-led enterprises")
            else:
                demographic_score += 10.0

        if profile.is_differently_abled:
            if scheme.disability_eligibility or any("differently-abled" in d.lower() for d in scheme.target_demographics):
                demographic_score += 10.0
                matching_factors.append("Special quota / subsidy boost for differently-abled entrepreneurs")

        # 2. Social Category Alignment (up to 30 pts)
        if profile.social_category:
            user_cat = profile.social_category.lower()
            scheme_cats = [c.lower() for c in (scheme.social_categories or scheme.target_demographics)]
            if user_cat in scheme_cats:
                category_score += 30.0
                matching_factors.append(f"Direct affirmative allocation for {profile.social_category} category")
            elif any(c in scheme_cats for c in ["sc", "st", "obc", "minority"]):
                category_score += 15.0
                matching_factors.append(f"Inclusive allocation covering marginalized groups")
            else:
                category_score += 10.0

        # 3. Business Sector & Operational Suitability (up to 25 pts)
        if scheme.eligible_business_types and len(scheme.eligible_business_types) > 0:
            target_types = [t.lower() for t in scheme.eligible_business_types]
            if profile.business_type and profile.business_type.lower() in target_types:
                business_score += 20.0
                matching_factors.append(f"Sector alignment: '{profile.business_type}' is an eligible sector")
            elif not profile.business_type:
                business_score += 10.0
            else:
                business_score += 5.0
        else:
            business_score += 15.0  # Open to all business sectors

        # Udyam alignment check
        if scheme.udyam_required:
            if profile.is_udyam_registered:
                business_score += 5.0
                matching_factors.append("Udyam registration verified")
            else:
                matching_factors.append("Action required: Free Udyam registration needed for disbursement")

        # 4. Baseline (10 pts)
        base_score = 10.0

        total_score = min(99.0, max(15.0, base_score + demographic_score + category_score + business_score))

        breakdown = ScoreBreakdown(
            demographic_score=demographic_score,
            business_score=business_score,
            category_score=category_score,
            semantic_score=0.0,
            hard_filter_passed=True
        )

        return round(total_score, 1), breakdown, matching_factors

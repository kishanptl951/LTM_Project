"""
Dual-Pass Contradiction Verifier:
Cross-examines narrative claims against footnote/notes disclosures.

US Market:  Item 7 MD&A narrative claims vs Item 8 Footnotes/disclosures.
India:      MD&A narrative claims vs Notes to Financial Statements.

Pass A: Retrieve management narrative claims.
Pass B: Retrieve related technical disclosures.
Analysis: Compare passages for qualification, contradiction, or material buried risk
          using LLM reasoning (Gemini) with heuristic fallback.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from src.config import GEMINI_API_KEY, LLM_VERIFIER_ENABLED, GEMINI_MODEL
from src.retrieval.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)

# Accounting risk signal terms used for heuristic contradiction detection (US)
_US_RISK_SIGNALS = [
    "impairment", "write-down", "write-off", "litigation",
    "contingent", "loss", "decline", "restatement", "restated",
    "material weakness", "adverse", "default", "penalty",
    "going concern", "uncertainty", "unfavorable", "overstate",
    "understate", "deficiency", "exposure", "breach",
    "settlement", "damages", "regulatory action",
]

# Indian-specific risk signals (SEBI / Companies Act)
_INDIAN_RISK_SIGNALS = [
    "promoter pledge", "pledged shares", "related party transaction",
    "contingent liability", "cdr", "npa", "non-performing",
    "stressed asset", "nclt", "ibc", "insolvency",
    "wilful defaulter", "forensic audit", "sebi order",
    "rbi directive", "promoter holding decrease", "pledge",
    "corporate guarantee", "inter-corporate deposit",
    "impairment", "write-off", "litigation", "contingent",
    "going concern", "adverse", "qualified opinion",
    "emphasis of matter", "material uncertainty",
    "regulatory action", "penalty", "show cause notice",
]

# Unified risk signals (merged)
_RISK_SIGNALS = list(set(_US_RISK_SIGNALS + _INDIAN_RISK_SIGNALS))

_US_QUALIFIER_SIGNALS = [
    "subject to", "may not", "cannot assure", "no assurance",
    "could adversely", "might not", "risk that", "there can be no",
    "except as", "net of", "partially offset", "excluding",
]

_INDIAN_QUALIFIER_SIGNALS = [
    "subject to approval", "pending resolution", "under review",
    "as per management", "to the best of our knowledge",
    "contingent upon", "notwithstanding", "pursuant to",
    "as directed by rbi", "as per sebi regulation",
]

_QUALIFIER_SIGNALS = list(set(_US_QUALIFIER_SIGNALS + _INDIAN_QUALIFIER_SIGNALS))


class ContradictionVerifier:
    """
    Performs dual-pass retrieval to cross-examine Item 7 (MD&A) executive
    narrative claims against Item 8 (Footnotes) disclosures for a given
    ticker and query topic. Supports LLM-based reasoning (Gemini API) with heuristic fallback.
    """

    def __init__(self, hybrid_engine: Optional[HybridSearchEngine] = None):
        self.hybrid_engine = hybrid_engine or HybridSearchEngine()

    def verify(
        self,
        query: Optional[str] = None,
        ticker: Optional[str] = None,
        top_k: int = 3,
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes dual-pass verification:
        1. Retrieves Item 7 (MD&A) passages related to the query topic.
        2. Retrieves Item 8 (Footnotes) passages on the same topic.
        3. Cross-examines both sets for contradictions, qualifications,
           or buried material risks.

        Returns:
            {
                "has_contradiction": bool,
                "severity": str,                 # "none", "qualification", "contradiction"
                "narrative_claims": [...],        # Item 7 passages
                "footnote_disclosures": [...],    # Item 8 passages
                "analysis": str,                  # Human-readable summary / LLM reasoning
                "risk_signals_found": [...],      # Specific risk terms detected
                "citations": [...],               # Combined citation list
                "verifier_mode": str,             # "LLM (Gemini)" or "Rule-based (Heuristic)"
            }
        """
        if not query or not query.strip():
            return self._empty_result(query)

        # Auto-detect market if not provided
        if market is None and ticker:
            from src.ingestion.market_router import detect_market
            market = detect_market(ticker)
        market = market or "US"

        # Determine section keys based on market
        if market == "INDIA":
            narrative_section = "mda"
            disclosure_section = "notes"
            narrative_label = "MD&A"
            disclosure_label = "Notes to Accounts"
        else:
            narrative_section = "item_7"
            disclosure_section = "item_8"
            narrative_label = "Item 7 (MD&A)"
            disclosure_label = "Item 8 (Footnotes)"

        # ------- Pass A: Retrieve Narrative Claims -------
        logger.info(f"Verifier Pass A: Retrieving {narrative_label} passages for '{query}'")
        narrative_results = self.hybrid_engine.search(
            query=query,
            top_k=top_k,
            section_filter=narrative_section,
            ticker_filter=ticker,
        )

        # ------- Pass B: Retrieve Technical Disclosures -------
        logger.info(f"Verifier Pass B: Retrieving {disclosure_label} passages for '{query}'")
        disclosure_results = self.hybrid_engine.search(
            query=query,
            top_k=top_k,
            section_filter=disclosure_section,
            ticker_filter=ticker,
        )

        # ------- Cross-Examination Analysis -------
        analysis_result = self._cross_examine(
            query, narrative_results, disclosure_results,
            narrative_label=narrative_label,
            disclosure_label=disclosure_label,
            market=market,
        )

        logger.info(
            f"Verifier complete for '{query}': "
            f"severity={analysis_result['severity']}, "
            f"has_contradiction={analysis_result['has_contradiction']}, "
            f"mode={analysis_result.get('verifier_mode')}"
        )

        return analysis_result

    def verify_discrepancy(self, narrative_claim: str, footnote_disclosure: str) -> Dict[str, Any]:
        """
        Legacy interface: accepts raw text strings instead of running retrieval.
        Performs cross-examination on the provided texts.
        """
        risk_signals = self._detect_risk_signals(footnote_disclosure)
        qualifiers = self._detect_qualifiers(footnote_disclosure)

        severity, has_contradiction = self._classify_severity(risk_signals, qualifiers)

        analysis_parts = []
        if risk_signals:
            analysis_parts.append(
                f"Footnote contains risk language: {', '.join(risk_signals[:5])}."
            )
        if qualifiers:
            analysis_parts.append(
                f"Footnote contains qualifying language: {', '.join(qualifiers[:5])}."
            )
        if not risk_signals and not qualifiers:
            analysis_parts.append(
                "No significant contradictions or qualifications detected between narrative and footnote."
            )

        return {
            "has_contradiction": has_contradiction,
            "severity": severity,
            "analysis": " ".join(analysis_parts),
            "risk_signals_found": risk_signals,
            "citations": [],
            "verifier_mode": "Rule-based (Heuristic)",
        }

    # ------------------------------------------------------------------
    # Internal analysis logic
    # ------------------------------------------------------------------

    def _cross_examine(
        self,
        query: str,
        narrative_results: List[Dict[str, Any]],
        disclosure_results: List[Dict[str, Any]],
        narrative_label: str = "Item 7 (MD&A)",
        disclosure_label: str = "Item 8 (Footnotes)",
        market: str = "US",
    ) -> Dict[str, Any]:
        """
        Cross-examination between narrative and disclosure passages.
        Uses LLM (Gemini API) if configured; falls back to rule-based heuristic.
        Market-aware: uses appropriate section labels for US vs India.
        """
        disclosure_text = " ".join(r.get("text", "") for r in disclosure_results)
        narrative_text = " ".join(r.get("text", "") for r in narrative_results)

        risk_signals = self._detect_risk_signals(disclosure_text, market)
        qualifiers = self._detect_qualifiers(disclosure_text, market)

        # Collect citations
        citations = []
        for r in narrative_results:
            if r.get("citation"):
                citations.append(r["citation"])
        for r in disclosure_results:
            if r.get("citation"):
                citations.append(r["citation"])

        # Try LLM Reasoning if enabled
        if LLM_VERIFIER_ENABLED and (narrative_text or disclosure_text):
            try:
                llm_res = self._llm_cross_examine(query, narrative_text, disclosure_text, market)
                if llm_res:
                    llm_res["narrative_claims"] = narrative_results
                    llm_res["footnote_disclosures"] = disclosure_results
                    llm_res["risk_signals_found"] = risk_signals
                    llm_res["citations"] = citations
                    llm_res["verifier_mode"] = "LLM (Gemini)"
                    return llm_res
            except Exception as e:
                logger.warning(f"LLM cross-examination failed ({e}). Falling back to heuristic mode.")

        # Heuristic Fallback
        severity, has_contradiction = self._classify_severity(risk_signals, qualifiers)

        analysis_parts = []
        if not narrative_results:
            analysis_parts.append(f"No {narrative_label} passages found for the query topic.")
        else:
            analysis_parts.append(f"Retrieved {len(narrative_results)} {narrative_label} passage(s).")

        if not disclosure_results:
            analysis_parts.append(f"No {disclosure_label} passages found for the query topic.")
        else:
            analysis_parts.append(f"Retrieved {len(disclosure_results)} {disclosure_label} passage(s).")

        if risk_signals:
            analysis_parts.append(
                f"FOOTNOTE RISK SIGNALS DETECTED: {', '.join(risk_signals[:8])}. "
                f"These may qualify or contradict management's narrative claims."
            )

        if qualifiers:
            analysis_parts.append(
                f"Qualifying language found in footnotes: {', '.join(qualifiers[:5])}."
            )

        if has_contradiction:
            analysis_parts.append(
                f"CONCLUSION: Material discrepancy detected between {narrative_label} narrative and {disclosure_label} disclosures. "
                "Manual review recommended."
            )
        elif risk_signals or qualifiers:
            analysis_parts.append(
                f"CONCLUSION: {disclosure_label} contains qualifying or risk language that may "
                f"temper the {narrative_label} claims. Further investigation advised."
            )
        else:
            analysis_parts.append(
                f"CONCLUSION: No significant contradictions detected between "
                f"{narrative_label} narrative and {disclosure_label} disclosures."
            )

        return {
            "has_contradiction": has_contradiction,
            "severity": severity,
            "narrative_claims": narrative_results,
            "footnote_disclosures": disclosure_results,
            "analysis": " ".join(analysis_parts),
            "risk_signals_found": risk_signals,
            "citations": citations,
            "verifier_mode": "Rule-based (Heuristic)",
        }

    def _llm_cross_examine(self, query: str, narrative_text: str, disclosure_text: str, market: str = "US") -> Optional[Dict[str, Any]]:
        """Invokes Gemini LLM to reason over narrative vs disclosure passages. Market-aware prompting."""
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)

            if market == "INDIA":
                regulatory_context = "Indian company's Annual Report (regulated by SEBI LODR and Companies Act, 2013)"
                narrative_label = "MANAGEMENT DISCUSSION & ANALYSIS (MD&A)"
                disclosure_label = "NOTES TO FINANCIAL STATEMENTS"
            else:
                regulatory_context = "SEC 10-K filing"
                narrative_label = "MD&A MANAGEMENT NARRATIVE (Item 7)"
                disclosure_label = "FOOTNOTE TECHNICAL DISCLOSURES (Item 8)"

            prompt = f"""You are a senior forensic financial auditor. Analyze the following passages from a company's {regulatory_context} for the query topic: "{query}".

{narrative_label}:
{narrative_text[:2500]}

{disclosure_label}:
{disclosure_text[:2500]}

Task:
Determine whether the disclosure passages contain facts, impairments, litigation, or qualifying language that CONTRADICT or MATERIALLY QUALIFY management's narrative claims.

Respond ONLY with a valid JSON object matching this structure:
{{
  "severity": "contradiction" | "qualification" | "none",
  "has_contradiction": true | false,
  "analysis": "A detailed 2-3 sentence forensic analysis explaining the verdict with specific references to the text."
}}
"""
            models_to_try = [GEMINI_MODEL]
            for m in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
                if m not in models_to_try:
                    models_to_try.append(m)

            response = None
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={"response_mime_type": "application/json", "temperature": 0},
                    )
                    if response and response.text:
                        break
                except Exception as m_err:
                    logger.warning(f"Gemini call with {model_name} failed: {m_err}. Trying next model...")

            if not response or not response.text:
                logger.warning("Gemini LLM returned an empty response or all models failed.")
                return None

            response_text = response.text.strip()
            # Clean Markdown codeblocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            parsed = json.loads(response_text)
            return {
                "has_contradiction": bool(parsed.get("has_contradiction", False)),
                "severity": str(parsed.get("severity", "none")).lower(),
                "analysis": f"[LLM Auditor Reasoning] {parsed.get('analysis', '')}",
            }
        except Exception as ex:
            logger.warning(f"Failed to execute Gemini LLM call: {ex}")
            return None

    def _detect_risk_signals(self, text: str, market: str = "US") -> List[str]:
        """Scans text for accounting risk signal terms. Uses market-appropriate signals."""
        text_lower = text.lower()
        signals = _INDIAN_RISK_SIGNALS if market == "INDIA" else _US_RISK_SIGNALS
        return [signal for signal in signals if signal in text_lower]

    def _detect_qualifiers(self, text: str, market: str = "US") -> List[str]:
        """Scans text for qualifying/hedging language. Uses market-appropriate qualifiers."""
        text_lower = text.lower()
        qualifiers = _INDIAN_QUALIFIER_SIGNALS if market == "INDIA" else _US_QUALIFIER_SIGNALS
        return [q for q in qualifiers if q in text_lower]

    def _classify_severity(
        self, risk_signals: List[str], qualifiers: List[str]
    ) -> tuple:
        """
        Classifies the severity of detected discrepancies.
        Returns (severity_label, has_contradiction).
        """
        if len(risk_signals) >= 3:
            return "contradiction", True
        elif risk_signals or len(qualifiers) >= 2:
            return "qualification", True
        else:
            return "none", False

    def _empty_result(self, query: Optional[str] = None) -> Dict[str, Any]:
        return {
            "has_contradiction": False,
            "severity": "none",
            "narrative_claims": [],
            "footnote_disclosures": [],
            "analysis": "Empty query provided.",
            "risk_signals_found": [],
            "citations": [],
            "verifier_mode": "N/A",
        }


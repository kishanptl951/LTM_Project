"""
Unit tests for Phase 4: DeterministicRouter and ContradictionVerifier.
"""
import pytest
from src.router.query_router import DeterministicRouter, QueryType
from src.router.verifier import ContradictionVerifier


# =====================================================================
# DeterministicRouter Tests
# =====================================================================

@pytest.fixture
def router():
    return DeterministicRouter()


class TestDeterministicRouter:
    """Tests for query classification and structured metadata extraction."""

    def test_numeric_route_with_full_metadata(self, router):
        """Router should extract ticker, concept, year, and period from a numeric query."""
        result = router.route_query("What was AAPL Q2 2026 Revenue?")
        assert result["route_type"] == QueryType.NUMERIC
        assert result["ticker"] == "AAPL"
        assert result["concept"] == "revenue"
        assert result["fiscal_year"] == 2026
        assert result["fiscal_period"] == "Q2"

    def test_numeric_route_net_income(self, router):
        """Router should map 'net income' to the canonical concept key."""
        result = router.route_query("TSLA net income for 2025 FY")
        assert result["route_type"] == QueryType.NUMERIC
        assert result["ticker"] == "TSLA"
        assert result["concept"] == "net_income"
        assert result["fiscal_year"] == 2025
        assert result["fiscal_period"] == "FY"

    def test_numeric_route_partial_metadata(self, router):
        """Router should still classify numeric even if year/period are missing."""
        result = router.route_query("What was AAPL total assets?")
        assert result["route_type"] == QueryType.NUMERIC
        assert result["ticker"] == "AAPL"
        assert result["concept"] == "total_assets"
        assert result["fiscal_year"] is None
        assert result["fiscal_period"] is None

    def test_numeric_route_comparison_query(self, router):
        """Comparison keywords should trigger numeric route."""
        result = router.route_query("Compare JPM Q1 vs Q3 2025 revenue growth")
        assert result["route_type"] == QueryType.NUMERIC
        assert result["ticker"] == "JPM"
        assert result["concept"] == "revenue"
        assert result["fiscal_year"] == 2025

    def test_narrative_route(self, router):
        """General qualitative queries should route to narrative."""
        result = router.route_query("What are the key supply chain risks for AAPL?")
        assert result["route_type"] == QueryType.NARRATIVE
        assert result["ticker"] == "AAPL"
        assert result["concept"] is None

    def test_narrative_route_section_filter(self, router):
        """Section references should be extracted as section_filter."""
        result = router.route_query("Show me TSLA Item 1A risk factors")
        assert result["route_type"] == QueryType.NARRATIVE
        assert result["ticker"] == "TSLA"
        assert result["section_filter"] == "item_1a"

    def test_narrative_override_query(self, router):
        """Queries containing financial concept words alongside narrative intent (risk, explain, outlook) should route to NARRATIVE."""
        res1 = router.route_query("What are Apple's supply chain risks that could affect future cash flow?")
        assert res1["route_type"] == QueryType.NARRATIVE
        assert res1["ticker"] == "AAPL"
        assert res1["concept"] == "operating_cash_flow"

        res2 = router.route_query("Explain the impact of inflation on Apple's net income")
        assert res2["route_type"] == QueryType.NARRATIVE
        assert res2["ticker"] == "AAPL"
        assert res2["concept"] == "net_income"


    def test_contradiction_route(self, router):
        """Contradiction keywords should trigger contradiction route."""
        result = router.route_query(
            "Check if AAPL Item 7 revenue claims contradict Item 8 footnotes"
        )
        assert result["route_type"] == QueryType.CONTRADICTION
        assert result["ticker"] == "AAPL"

    def test_contradiction_route_audit_keyword(self, router):
        """'audit' keyword should trigger contradiction route."""
        result = router.route_query("Audit RMD 2024 inventory discrepancies")
        assert result["route_type"] == QueryType.CONTRADICTION
        assert result["ticker"] == "RMD"
        assert result["fiscal_year"] == 2024

    def test_contradiction_route_verify_keyword(self, router):
        """'verify' keyword should trigger contradiction route."""
        result = router.route_query("Verify TSLA footnote mismatch on revenue recognition")
        assert result["route_type"] == QueryType.CONTRADICTION
        assert result["ticker"] == "TSLA"
        assert result["concept"] == "revenue"

    def test_empty_query(self, router):
        """Empty query should default to narrative route."""
        result = router.route_query("")
        assert result["route_type"] == QueryType.NARRATIVE
        assert result["ticker"] is None

    def test_route_result_structure(self, router):
        """Every route result should contain all expected keys."""
        result = router.route_query("AAPL Q1 2026 Revenue")
        expected_keys = {
            "route_type", "ticker", "concept",
            "fiscal_year", "fiscal_years", "fiscal_period", "section_filter", "raw_query"
        }
        assert set(result.keys()) == expected_keys

    def test_case_insensitive_ticker(self, router):
        """Ticker extraction should be case-insensitive."""
        result = router.route_query("what was aapl revenue in 2025?")
        assert result["ticker"] == "AAPL"

    def test_multi_word_concept_priority(self, router):
        """Multi-word concepts like 'net income' should match before 'income'."""
        result = router.route_query("AAPL net income 2025")
        assert result["concept"] == "net_income"

    def test_company_name_mapping(self, router):
        """Company names like 'Apple' or 'Tesla' or 'Pfizer' should resolve to tickers."""
        result = router.route_query("What was Apple revenue in 2023?")
        assert result["ticker"] == "AAPL"

        result_pfe = router.route_query("Pfizer capex in 2024")
        assert result_pfe["ticker"] == "PFE"
        assert result_pfe["concept"] == "capital_expenditure"

    def test_expanded_concept_keywords(self, router):
        """Router should extract operating_cash_flow, capex, and rnd_expense."""
        res_ocf = router.route_query("What was AAPL 2025 operating cash flow?")
        assert res_ocf["concept"] == "operating_cash_flow"

        res_rnd = router.route_query("NVDA research and development expense 2026")
        assert res_rnd["concept"] == "rnd_expense"

    def test_restatement_route(self, router):
        """Restatement keywords should trigger restatement route."""
        result = router.route_query("Did Apple restate 2024 revenue figures in amended filings?")
        assert result["route_type"] == QueryType.RESTATEMENT
        assert result["ticker"] == "AAPL"
        assert result["concept"] == "revenue"



# =====================================================================
# ContradictionVerifier Tests
# =====================================================================

class TestContradictionVerifier:
    """Tests for dual-pass verification logic."""

    def test_verify_discrepancy_with_risk_signals(self):
        """Legacy interface should detect risk signals in footnote text."""
        verifier = ContradictionVerifier()
        result = verifier.verify_discrepancy(
            narrative_claim="The Company experienced strong revenue growth.",
            footnote_disclosure=(
                "The Company recorded an impairment charge of $500M related to "
                "inventory write-down. A litigation settlement of $200M is pending. "
                "There is material weakness in internal controls."
            ),
        )
        assert result["has_contradiction"] is True
        assert result["severity"] == "contradiction"
        assert "impairment" in result["risk_signals_found"]
        assert "write-down" in result["risk_signals_found"]
        assert "litigation" in result["risk_signals_found"]

    def test_verify_discrepancy_with_qualifiers_only(self):
        """Should detect qualification when only qualifying language is present."""
        verifier = ContradictionVerifier()
        result = verifier.verify_discrepancy(
            narrative_claim="Revenue increased significantly.",
            footnote_disclosure=(
                "Revenue is subject to seasonal variations and may not "
                "continue at current levels. There can be no assurance "
                "that growth will persist."
            ),
        )
        assert result["has_contradiction"] is True
        assert result["severity"] == "qualification"

    def test_verify_discrepancy_no_contradiction(self):
        """Should return no contradiction when footnote has no risk language."""
        verifier = ContradictionVerifier()
        result = verifier.verify_discrepancy(
            narrative_claim="The Company maintained stable operations.",
            footnote_disclosure="Revenue recognition follows ASC 606 standards.",
        )
        assert result["has_contradiction"] is False
        assert result["severity"] == "none"

    def test_verify_empty_query(self):
        """Verify should handle empty query gracefully."""
        verifier = ContradictionVerifier()
        result = verifier.verify(query="")
        assert result["has_contradiction"] is False
        assert result["severity"] == "none"
        assert result["narrative_claims"] == []
        assert result["footnote_disclosures"] == []

    def test_verify_result_structure(self):
        """Full verify result should contain all expected keys."""
        verifier = ContradictionVerifier()
        result = verifier.verify(query="test query")
        expected_keys = {
            "has_contradiction", "severity",
            "narrative_claims", "footnote_disclosures",
            "analysis", "risk_signals_found", "citations",
            "verifier_mode",
        }
        assert set(result.keys()) == expected_keys

    def test_llm_cross_examine_none_response(self, monkeypatch):
        """Should return None gracefully without raising AttributeError when LLM response text is None."""
        class MockResponse:
            text = None

        class MockModels:
            def generate_content(self, model, contents):
                return MockResponse()

        class MockClient:
            models = MockModels()

        monkeypatch.setattr("google.genai.Client", lambda api_key: MockClient())
        verifier = ContradictionVerifier()
        result = verifier._llm_cross_examine("query", "narrative", "footnote")
        assert result is None


# =====================================================================
# Indian Market Router Tests
# =====================================================================

class TestDeterministicRouterIndianMarket:
    """Tests for Indian company name mapping, concepts, and section filters."""

    @pytest.fixture
    def router(self):
        return DeterministicRouter()

    # --- Indian Company Name Mapping ---

    def test_reliance_name_mapping(self, router):
        result = router.route_query("What was Reliance FY 2024 Revenue?")
        assert result["ticker"] == "RELIANCE.NS"
        assert result["concept"] == "revenue"
        assert result["market"] == "INDIA"

    def test_tcs_name_mapping(self, router):
        result = router.route_query("TCS net income for 2024")
        assert result["ticker"] == "TCS.NS"
        assert result["concept"] == "net_income"

    def test_hdfc_bank_name_mapping(self, router):
        result = router.route_query("HDFC Bank total assets 2024")
        assert result["ticker"] == "HDFCBANK.NS"
        assert result["concept"] == "total_assets"

    def test_infosys_name_mapping(self, router):
        result = router.route_query("Infosys revenue growth 2024")
        assert result["ticker"] == "INFY.NS"

    def test_adani_name_mapping(self, router):
        result = router.route_query("Adani cash flow 2024")
        assert result["ticker"] == "ADANIENT.NS"

    # --- Indian Concept Keywords ---

    def test_turnover_maps_to_revenue(self, router):
        result = router.route_query("What was RELIANCE.NS turnover in 2024?")
        assert result["concept"] == "revenue"
        assert result["route_type"] == QueryType.NUMERIC

    def test_pat_maps_to_net_income(self, router):
        result = router.route_query("TCS.NS PAT for FY 2024")
        assert result["concept"] == "net_income"
        assert result["route_type"] == QueryType.NUMERIC

    def test_profit_after_tax_maps_to_net_income(self, router):
        result = router.route_query("What was Infosys profit after tax 2024?")
        assert result["concept"] == "net_income"

    def test_pbt_maps_to_operating_income(self, router):
        result = router.route_query("HDFCBANK.NS PBT 2024")
        assert result["concept"] == "operating_income"

    # --- Indian Section Filters ---

    def test_board_report_section_filter(self, router):
        result = router.route_query("What does the board report say about Reliance governance?")
        assert result["section_filter"] == "board_report"

    def test_notes_to_accounts_section_filter(self, router):
        result = router.route_query("Check notes to accounts for TCS related party transactions")
        assert result["section_filter"] == "notes"

    def test_auditor_report_section_filter(self, router):
        result = router.route_query("What did the auditor report say about Infosys?")
        assert result["section_filter"] == "auditor_report"

    # --- Market Detection in Results ---

    def test_us_ticker_market_is_us(self, router):
        result = router.route_query("AAPL revenue 2024")
        assert result["market"] == "US"

    def test_indian_ticker_market_is_india(self, router):
        result = router.route_query("RELIANCE.NS revenue 2024")
        assert result["market"] == "INDIA"

    def test_indian_company_name_market_is_india(self, router):
        result = router.route_query("What was Tata Motors revenue in 2024?")
        assert result["ticker"] == "TATAMOTORS.NS"
        assert result["market"] == "INDIA"

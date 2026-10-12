from datetime import date

from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    DamagePhotoDocument,
    PolicyDocument,
    PoliceReportDocument,
    RepairEstimateDocument,
)


def build_base_claim():
    return Claim(
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date=date(2026, 9, 5),
        reported_date=date(2026, 9, 6),
        vehicle_registration="TS09AB1234",
    )


def build_base_policy():
    return PolicyDocument(
        policy_number="POL-2026-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
        deductible=10000.0,
        coverage_limit=100000.0,
    )


def build_base_claim_form():
    return ClaimFormDocument(
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date=date(2026, 9, 5),
        reported_date=date(2026, 9, 6),
        vehicle_registration="TS09AB1234",
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )


# ============================================================
# 1. COMPLETELY CONSISTENT CLAIM
# ============================================================


def test_consistent_claim_package():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    police_report = PoliceReportDocument(
        report_number="FIR-001",
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        incident_date=date(2026, 9, 5),
        incident_location="Hyderabad",
        vehicle_registration="TS09AB1234",
    )

    damage_photo = DamagePhotoDocument(
        claim_id="ADV-001",
        vehicle_registration="TS09AB1234",
        damage_area="front bumper",
        visible_damage="front bumper dent and scratches",
        estimated_severity="moderate",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
        damage_photo=damage_photo,
    )

    assert assessment.overall_result == "PASS"

    assert all(
        result.result == "PASS"
        for result in assessment.policy_results
    )

    assert all(
        result.result == "PASS"
        for result in assessment.invariant_results
    )

    assert len(assessment.damage_results) == 1
    assert assessment.damage_results[0].result == "PASS"


# ============================================================
# 2. POLICY VEHICLE MISMATCH
# ============================================================


def test_policy_vehicle_mismatch():

    claim = build_base_claim()
    policy = build_base_policy()
    policy.vehicle_registration = "TS09XY5678"

    claim_form = build_base_claim_form()

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
    )

    assert assessment.overall_result in {"FAIL", "REVIEW"}

    assert any(
        result.result == "FAIL"
        for result in assessment.invariant_results
    )


# ============================================================
# 3. POLICE REPORT VEHICLE MISMATCH
# ============================================================


def test_police_report_vehicle_mismatch():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    police_report = PoliceReportDocument(
        report_number="FIR-002",
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09XY5678",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
    )

    assert assessment.overall_result in {"FAIL", "REVIEW"}

    assert any(
        result.result == "FAIL"
        for result in assessment.invariant_results
    )


# ============================================================
# 4. INCIDENT DATE MISMATCH
# ============================================================


def test_incident_date_mismatch():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    police_report = PoliceReportDocument(
        report_number="FIR-003",
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        incident_date=date(2026, 9, 7),
        vehicle_registration="TS09AB1234",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
    )

    assert assessment.overall_result in {"FAIL", "REVIEW"}

    assert any(
        result.result == "FAIL"
        for result in assessment.invariant_results
    )


# ============================================================
# 5. REPAIR COST EXCEEDS COVERAGE
# ============================================================


def test_repair_cost_exceeds_coverage():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    repair_estimate = RepairEstimateDocument(
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        vehicle_registration="TS09AB1234",
        total_estimated_cost=150000.0,
        parts_cost=100000.0,
        labor_cost=50000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert assessment.overall_result == "REVIEW"

    assert any(
        result.result == "REVIEW"
        for result in assessment.expense_results
    )


# ============================================================
# 6. REPAIR COMPONENT MISMATCH
# ============================================================


def test_repair_component_mismatch():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    repair_estimate = RepairEstimateDocument(
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        vehicle_registration="TS09AB1234",
        total_estimated_cost=90000.0,
        parts_cost=50000.0,
        labor_cost=20000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert assessment.overall_result == "REVIEW"

    assert any(
        result.result == "REVIEW"
        for result in assessment.expense_results
    )


# ============================================================
# 7. DAMAGE AREA MISMATCH
# ============================================================


def test_damage_area_mismatch():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    damage_photo = DamagePhotoDocument(
        claim_id="ADV-001",
        vehicle_registration="TS09AB1234",
        damage_area="rear bumper",
        visible_damage="rear bumper dent",
        estimated_severity="moderate",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert assessment.overall_result == "REVIEW"

    assert len(assessment.damage_results) == 1

    assert (
        assessment.damage_results[0].result
        == "REVIEW"
    )


# ============================================================
# 8. MULTIPLE SIMULTANEOUS INCONSISTENCIES
# ============================================================


def test_multiple_simultaneous_inconsistencies():

    claim = build_base_claim()

    policy = build_base_policy()
    policy.vehicle_registration = "TS09XY5678"

    claim_form = build_base_claim_form()

    police_report = PoliceReportDocument(
        report_number="FIR-004",
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        incident_date=date(2026, 9, 7),
        vehicle_registration="TS09ZZ9999",
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        vehicle_registration="TS09AB1234",
        total_estimated_cost=150000.0,
        parts_cost=50000.0,
        labor_cost=20000.0,
    )

    damage_photo = DamagePhotoDocument(
        claim_id="ADV-001",
        vehicle_registration="TS09AB1234",
        damage_area="rear bumper",
        visible_damage="rear bumper dent",
        estimated_severity="severe",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
        repair_estimate=repair_estimate,
        damage_photo=damage_photo,
    )

    assert assessment.overall_result in {"FAIL", "REVIEW"}

    assert len(assessment.reasons) >= 3

    assert any(
        result.result == "FAIL"
        for result in assessment.invariant_results
    )

    assert any(
        result.result == "REVIEW"
        for result in assessment.expense_results
    )

    assert any(
        result.result == "REVIEW"
        for result in assessment.damage_results
    )


# ============================================================
# 9. MISSING DAMAGE PHOTO
# ============================================================


def test_missing_required_damage_photo():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
    )

    assert assessment.overall_result == "REVIEW"

    assert "DAMAGE_PHOTO" in assessment.missing_documents

    assert any(
        "DAMAGE_PHOTO" in reason
        for reason in assessment.reasons
    )


# ============================================================
# 10. INCOMPLETE REPAIR ESTIMATE
# ============================================================


def test_incomplete_repair_estimate():

    claim = build_base_claim()
    policy = build_base_policy()
    claim_form = build_base_claim_form()

    repair_estimate = RepairEstimateDocument(
        claim_id="ADV-001",
        policy_number="POL-2026-001",
        vehicle_registration="TS09AB1234",
        total_estimated_cost=80000.0,
        parts_cost=None,
        labor_cost=20000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert assessment.overall_result == "REVIEW"

    assert any(
        result.result == "REVIEW"
        for result in assessment.expense_results
    )
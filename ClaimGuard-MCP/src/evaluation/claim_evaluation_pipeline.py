from src.evaluation.claim_assessment_service import ClaimAssessmentService
from src.evaluation.damage_consistency_service import (
    DamageConsistencyService,
)
from src.evaluation.document_requirement_service import (
    DocumentRequirementService,
)
from src.evaluation.invariant_evaluation_service import (
    InvariantEvaluationService,
)
from src.evaluation.policy_evaluation_service import (
    PolicyEvaluationService,
)
from src.evaluation.expense_evaluation_service import (
    ExpenseEvaluationService,
)
from src.evaluation.expense_consistency_service import (
    ExpenseConsistencyService,
)
from src.models.schemas import (
    Claim,
    ClaimAssessment,
    ClaimFormDocument,
    DamagePhotoDocument,
    MedicalBillDocument,
    PolicyDocument,
    PoliceReportDocument,
    RepairEstimateDocument,
)
from src.services.evidence_service import EvidenceService


class ClaimEvaluationPipeline:

    def __init__(self) -> None:
        self.policy_evaluation_service = PolicyEvaluationService()
        self.invariant_evaluation_service = InvariantEvaluationService()
        self.expense_evaluation_service = ExpenseEvaluationService()
        self.expense_consistency_service = ExpenseConsistencyService()
        self.damage_consistency_service = DamageConsistencyService()
        self.claim_assessment_service = ClaimAssessmentService()
        self.document_requirement_service = DocumentRequirementService()
        self.evidence_service = EvidenceService()

    def evaluate_claim(
        self,
        claim: Claim,
        policy: PolicyDocument,
        claim_form: ClaimFormDocument,
        police_report: PoliceReportDocument | None = None,
        repair_estimate: RepairEstimateDocument | None = None,
        damage_photo: DamagePhotoDocument | None = None,
        damage_photos: list[DamagePhotoDocument] | None = None,
        medical_bill: MedicalBillDocument | None = None,
        evidence_count: int | None = None,
    ) -> ClaimAssessment:

        # Step 1: Evaluate the claim against the policy.
        policy_results = self.policy_evaluation_service.evaluate_claim(
            claim=claim,
            policy=policy,
        )

        # Step 2: Check consistency between claim documents.

        vehicle_result = (
            self.invariant_evaluation_service.check_vehicle_registration(
                claim_form=claim_form,
                policy=policy,
            )
        )

        policy_number_result = (
            self.invariant_evaluation_service.check_policy_number(
                claim_form=claim_form,
                policy=policy,
            )
        )

        claimant_name_result = (
            self.invariant_evaluation_service.check_claimant_name(
                claim_form=claim_form,
                policy=policy,
            )
        )

        vehicle_police_result = None
        incident_date_result = None

        if police_report is not None:

            # Only compare vehicle registrations when the
            # police report actually contains one.
            if police_report.vehicle_registration:
                vehicle_police_result = (
                    self.invariant_evaluation_service
                    .check_vehicle_registration_against_police_report(
                        claim_form=claim_form,
                        police_report=police_report,
                    )
                )

            incident_date_result = (
                self.invariant_evaluation_service.check_incident_date(
                    claim_form=claim_form,
                    police_report=police_report,
                )
            )

        invariant_results = [
            vehicle_result,
            policy_number_result,
            claimant_name_result,
        ]

        if vehicle_police_result is not None:
            invariant_results.append(vehicle_police_result)

        if incident_date_result is not None:
            invariant_results.append(incident_date_result)

        # Step 3: Evaluate repair expenses when a repair estimate
        # is available.
        expense_results = []

        if repair_estimate is not None:

            # Check repair cost against the policy coverage limit.
            expense_result = (
                self.expense_evaluation_service.evaluate_repair_cost(
                    claim=claim,
                    policy=policy,
                    repair_estimate=repair_estimate,
                )
            )

            expense_results.append(expense_result)

            # Check whether parts + labor reconcile with
            # the declared total repair cost.
            consistency_result = (
                self.expense_consistency_service.validate_repair_estimate(
                    repair_estimate=repair_estimate,
                )
            )

            expense_results.append(consistency_result)

        # Step 4: Evaluate damage consistency when damage photo(s)
        # observations are available.
        damage_results = []
        all_damage_photos: list[DamagePhotoDocument] = []
        if damage_photo is not None:
            all_damage_photos.append(damage_photo)
        if damage_photos:
            for dp in damage_photos:
                if dp not in all_damage_photos:
                    all_damage_photos.append(dp)

        for photo in all_damage_photos:
            damage_result = (
                self.damage_consistency_service.compare_damage(
                    claim_form=claim_form,
                    damage_photo=photo,
                )
            )
            damage_results.append(damage_result)

        # Step 5: Determine required documents.
        required_documents = (
            self.document_requirement_service.get_required_documents(
                claim
            )
        )

        # Step 6: Determine which required documents are available.
        available_documents = {
            "CLAIM_FORM",
            "POLICY",
        }

        if police_report is not None:
            available_documents.add("POLICE_REPORT")

        if all_damage_photos:
            available_documents.add("DAMAGE_PHOTO")

        if repair_estimate is not None:
            available_documents.add("REPAIR_ESTIMATE")

        if medical_bill is not None:
            available_documents.add("MEDICAL_BILL")

        missing_documents = [
            document
            for document in required_documents
            if document not in available_documents
        ]

        # Step 7: Retrieve the real evidence stored during extraction.
        evidence = self.evidence_service.get_claim_evidence(
            claim.claim_id
        )

        actual_evidence_count = len(evidence)

        # Allow an explicit count when an existing caller provides one.
        if evidence_count is not None:
            actual_evidence_count = evidence_count

        # Step 8: Combine all results into one claim assessment.
        assessment = self.claim_assessment_service.assess_claim(
            claim=claim,
            policy_results=policy_results,
            invariant_results=invariant_results,
            expense_results=expense_results,
            damage_results=damage_results,
            evidence_count=actual_evidence_count,
            required_documents=required_documents,
            available_documents=sorted(available_documents),
            missing_documents=missing_documents,
        )

        return assessment
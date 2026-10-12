from src.models.schemas import Claim


class DocumentRequirementService:

    def get_required_documents(self, claim: Claim) -> list[str]:
        """
        Determine which documents are required for a claim.
        """

        required_documents = [
            "CLAIM_FORM",
            "POLICY",
        ]

        if claim.claim_type:
            claim_type = claim.claim_type.strip().lower()

            if "motor" in claim_type or "vehicle" in claim_type:
                required_documents.append("DAMAGE_PHOTO")

        return required_documents

    def get_conditional_documents(self, claim: Claim) -> list[str]:
        """
        Determine which documents may be required depending
        on the circumstances of the claim.
        """

        conditional_documents = []

        if claim.claim_type:
            claim_type = claim.claim_type.strip().lower()

            if "motor" in claim_type or "vehicle" in claim_type:
                conditional_documents.append("POLICE_REPORT")

        return conditional_documents
from src.db.session import get_db_connection
from src.models.schemas import ExtractedEvidence


class EvidenceService:

    def save_evidence(self, evidence: ExtractedEvidence) -> None:
        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO extracted_evidence (
                    evidence_id,
                    claim_id,
                    document_id,
                    field_name,
                    field_value,
                    confidence,
                    page_number,
                    evidence_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (evidence_id) DO UPDATE SET
                    claim_id = excluded.claim_id,
                    document_id = excluded.document_id,
                    field_name = excluded.field_name,
                    field_value = excluded.field_value,
                    confidence = excluded.confidence,
                    page_number = excluded.page_number,
                    evidence_text = excluded.evidence_text
                """,
                [
                    evidence.evidence_id,
                    evidence.claim_id,
                    evidence.document_id,
                    evidence.field_name,
                    evidence.field_value,
                    evidence.confidence,
                    evidence.page_number,
                    evidence.evidence_text,
                ],
            )

    def get_claim_evidence(
        self,
        claim_id: str,
    ) -> list[ExtractedEvidence]:
        with get_db_connection() as conn:

            results = conn.execute(
                """
                SELECT
                    evidence_id,
                    claim_id,
                    document_id,
                    field_name,
                    field_value,
                    confidence,
                    page_number,
                    evidence_text,
                    created_at
                FROM extracted_evidence
                WHERE claim_id = ?
                ORDER BY created_at
                """,
                [claim_id],
            ).fetchall()

        return [
            ExtractedEvidence(
                evidence_id=row[0],
                claim_id=row[1],
                document_id=row[2],
                field_name=row[3],
                field_value=row[4],
                confidence=row[5],
                page_number=row[6],
                evidence_text=row[7],
                created_at=row[8],
            )
            for row in results
        ]
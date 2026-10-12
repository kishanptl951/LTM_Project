from src.db.session import get_db_connection
from src.models.schemas import InvariantResult


class InvariantService:

    def save_result(self, result: InvariantResult) -> None:
        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO invariant_results (
                    result_id,
                    claim_id,
                    invariant_id,
                    result,
                    severity,
                    explanation
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (result_id) DO UPDATE SET
                    claim_id = excluded.claim_id,
                    invariant_id = excluded.invariant_id,
                    result = excluded.result,
                    severity = excluded.severity,
                    explanation = excluded.explanation
                """,
                [
                    result.result_id,
                    result.claim_id,
                    result.invariant_id,
                    result.result,
                    result.severity,
                    result.explanation,
                ],
            )

    def get_claim_results(
        self,
        claim_id: str,
    ) -> list[InvariantResult]:
        with get_db_connection() as conn:

            results = conn.execute(
                """
                SELECT
                    result_id,
                    claim_id,
                    invariant_id,
                    result,
                    severity,
                    explanation,
                    created_at
                FROM invariant_results
                WHERE claim_id = ?
                ORDER BY created_at
                """,
                [claim_id],
            ).fetchall()

        return [
            InvariantResult(
                result_id=row[0],
                claim_id=row[1],
                invariant_id=row[2],
                result=row[3],
                severity=row[4],
                explanation=row[5],
                created_at=row[6],
            )
            for row in results
        ]
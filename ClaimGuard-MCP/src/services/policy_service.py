from src.db.session import get_db_connection
from src.models.schemas import PolicyEvaluation


class PolicyService:

    def save_evaluation(self, evaluation: PolicyEvaluation) -> None:
        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO policy_evaluations (
                    evaluation_id,
                    claim_id,
                    rule_id,
                    result,
                    explanation,
                    repair_cost,
                    coverage_limit,
                    deductible,
                    estimated_payable
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (evaluation_id) DO UPDATE SET
                    claim_id = excluded.claim_id,
                    rule_id = excluded.rule_id,
                    result = excluded.result,
                    explanation = excluded.explanation,
                    repair_cost = excluded.repair_cost,
                    coverage_limit = excluded.coverage_limit,
                    deductible = excluded.deductible,
                    estimated_payable = excluded.estimated_payable
                """,
                [
                    evaluation.evaluation_id,
                    evaluation.claim_id,
                    evaluation.rule_id,
                    evaluation.result,
                    evaluation.explanation,
                    evaluation.repair_cost,
                    evaluation.coverage_limit,
                    evaluation.deductible,
                    evaluation.estimated_payable,
                ],
            )

    def get_claim_evaluations(
        self,
        claim_id: str,
    ) -> list[PolicyEvaluation]:
        with get_db_connection() as conn:

            results = conn.execute(
                """
                SELECT
                    evaluation_id,
                    claim_id,
                    rule_id,
                    result,
                    explanation,
                    repair_cost,
                    coverage_limit,
                    deductible,
                    estimated_payable,
                    created_at
                FROM policy_evaluations
                WHERE claim_id = ?
                ORDER BY created_at
                """,
                [claim_id],
            ).fetchall()

        return [
            PolicyEvaluation(
                evaluation_id=row[0],
                claim_id=row[1],
                rule_id=row[2],
                result=row[3],
                explanation=row[4],
                repair_cost=row[5],
                coverage_limit=row[6],
                deductible=row[7],
                estimated_payable=row[8],
                created_at=row[9],
            )
            for row in results
        ]
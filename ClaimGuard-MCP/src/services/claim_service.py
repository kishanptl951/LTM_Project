from src.db.session import get_db_connection
from src.models.schemas import Claim


class ClaimService:

    def create_claim(self, claim: Claim) -> None:
        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO claims (
                    claim_id,
                    policy_number,
                    claimant_name,
                    claim_type,
                    incident_date,
                    reported_date,
                    vehicle_registration,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (claim_id) DO UPDATE SET
                    policy_number = excluded.policy_number,
                    claimant_name = excluded.claimant_name,
                    claim_type = excluded.claim_type,
                    incident_date = excluded.incident_date,
                    reported_date = excluded.reported_date,
                    vehicle_registration = excluded.vehicle_registration,
                    status = excluded.status
                """,
                [
                    claim.claim_id,
                    claim.policy_number or "",
                    claim.claimant_name,
                    claim.claim_type,
                    claim.incident_date,
                    claim.reported_date,
                    claim.vehicle_registration,
                    claim.status,
                ],
            )

    def update_claim_status(self, claim_id: str, status: str) -> None:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE claims SET status = ? WHERE claim_id = ?",
                [status, claim_id],
            )

    def get_claim(self, claim_id: str) -> Claim | None:
        with get_db_connection() as conn:

            result = conn.execute(
                """
                SELECT
                    claim_id,
                    policy_number,
                    claimant_name,
                    claim_type,
                    incident_date,
                    reported_date,
                    vehicle_registration,
                    status,
                    created_at
                FROM claims
                WHERE claim_id = ?
                """,
                [claim_id],
            ).fetchone()

        if result is None:
            return None

        return Claim(
            claim_id=result[0],
            policy_number=result[1],
            claimant_name=result[2],
            claim_type=result[3],
            incident_date=result[4],
            reported_date=result[5],
            vehicle_registration=result[6],
            status=result[7],
            created_at=result[8],
        )
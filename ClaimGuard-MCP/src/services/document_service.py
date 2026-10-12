from pathlib import Path

from src.db.session import get_db_connection
from src.models.schemas import ClaimDocument


class DocumentService:

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    def register_document(self, document: ClaimDocument) -> None:
        file_path = Path(document.file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Document file not found: {document.file_path}"
            )

        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {file_path.suffix}"
            )

        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO documents (
                    document_id,
                    claim_id,
                    document_type,
                    file_name,
                    file_path
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (document_id) DO UPDATE SET
                    claim_id = excluded.claim_id,
                    document_type = excluded.document_type,
                    file_name = excluded.file_name,
                    file_path = excluded.file_path
                """,
                [
                    document.document_id,
                    document.claim_id,
                    document.document_type,
                    document.file_name,
                    str(file_path),
                ],
            )

    def get_document(self, document_id: str) -> ClaimDocument | None:
        with get_db_connection() as conn:

            result = conn.execute(
                """
                SELECT
                    document_id,
                    claim_id,
                    document_type,
                    file_name,
                    file_path,
                    created_at
                FROM documents
                WHERE document_id = ?
                """,
                [document_id],
            ).fetchone()

        if result is None:
            return None

        return ClaimDocument(
            document_id=result[0],
            claim_id=result[1],
            document_type=result[2],
            file_name=result[3],
            file_path=result[4],
            created_at=result[5],
        )
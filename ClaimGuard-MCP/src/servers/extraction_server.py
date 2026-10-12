from pathlib import Path

from mcp.server.mcpserver import MCPServer

from src.extraction.claim_extraction_pipeline import ClaimExtractionPipeline
from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)


mcp = MCPServer("ClaimGuard Extraction Server")

pipeline = ClaimExtractionPipeline()
structured_extraction_service = StructuredExtractionService()


@mcp.tool()
def extract_claim_document(
    file_path: str,
    claim_id: str,
    document_id: str,
) -> list[dict]:
    """
    Extract structured evidence from an insurance claim document.

    Supports PDF and image documents.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    evidence = pipeline.process_document(
        file_path=str(path),
        claim_id=claim_id,
        document_id=document_id,
    )

    return [
        item.model_dump(mode="json")
        for item in evidence
    ]


@mcp.tool()
def extract_structured_document(
    file_path: str,
    claim_id: str,
    document_id: str,
) -> dict:
    """
    Extract a document from a PDF/image and map it
    into its typed ClaimGuard document model.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    document = structured_extraction_service.process_and_map_document(
        file_path=str(path),
        claim_id=claim_id,
        document_id=document_id,
    )

    return {
        "document_type": type(document).__name__,
        "data": document.model_dump(mode="json"),
    }


if __name__ == "__main__":
    mcp.run()
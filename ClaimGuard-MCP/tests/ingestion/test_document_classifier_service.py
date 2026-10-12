from pathlib import Path

from src.ingestion.document_classifier_service import (
    DocumentClassifierService,
    DocumentType,
)


def test_classify_policy():
    service = DocumentClassifierService()

    file_path = Path("data/sample_claims/test_policy.pdf")
    file_path.touch()

    text = """
    Insurance Policy
    Policy Number: POL-2026-001
    Policy Period: 2026-01-01 to 2026-12-31
    Coverage: Comprehensive Motor Insurance
    Premium: INR 25,000
    """

    result = service.classify(
        file_path=str(file_path),
        text=text,
    )

    assert result == DocumentType.POLICY


def test_classify_police_report():
    service = DocumentClassifierService()

    file_path = Path("data/sample_claims/test_police_report.pdf")
    file_path.touch()

    text = """
    Police Report
    FIR Number: HYD-2026-0915
    Police Station: Hyderabad Central
    Incident Date: 2026-09-05
    """

    result = service.classify(
        file_path=str(file_path),
        text=text,
    )

    assert result == DocumentType.POLICE_REPORT


def test_classify_medical_bill():
    service = DocumentClassifierService()

    file_path = Path("data/sample_claims/test_medical_bill.pdf")
    file_path.touch()

    text = """
    Hospital Medical Bill
    Hospital: City Care Hospital
    Patient: Rahul Sharma
    Treatment Date: 2026-09-05
    Total Amount: INR 45,000
    """

    result = service.classify(
        file_path=str(file_path),
        text=text,
    )

    assert result == DocumentType.MEDICAL_BILL


def test_classify_repair_estimate():
    service = DocumentClassifierService()

    file_path = Path("data/sample_claims/test_repair_estimate.pdf")
    file_path.touch()

    text = """
    Vehicle Repair Estimate
    Vehicle Registration: TS09AB1234
    Repair Cost: INR 85,000
    Labor Charges: INR 15,000
    """

    result = service.classify(
        file_path=str(file_path),
        text=text,
    )

    assert result == DocumentType.REPAIR_ESTIMATE


def test_classify_claim_form():
    service = DocumentClassifierService()

    file_path = Path("data/sample_claims/test_claim_form.pdf")
    file_path.touch()

    text = """
    Insurance Claim Form
    Claim ID: CLM-001
    Incident Date: 2026-09-05
    Claimant Name: Rahul Sharma
    """

    result = service.classify(
        file_path=str(file_path),
        text=text,
    )

    assert result == DocumentType.CLAIM_FORM


def test_classify_damage_photo():
    service = DocumentClassifierService()

    file_path = Path("data/sample_claims/test_damage.jpg")
    file_path.touch()

    result = service.classify(
        file_path=str(file_path),
        text=None,
    )

    assert result == DocumentType.DAMAGE_PHOTO


class FakeExtractionService:

    def __init__(self, ocr_text: str = ""):
        self.ocr_text = ocr_text

    def extract_text_from_image(self, file_path: str) -> str:
        return self.ocr_text

    def extract_text_from_pdf(self, file_path: str) -> str:
        return self.ocr_text


def test_classify_scanned_police_report_image():
    extractor = FakeExtractionService(
        ocr_text="""
        FIRST INFORMATION REPORT (FIR)
        FIR Number: POL-9921
        Police Station: Jubilee Hills
        Incident Date: 2026-09-10
        """
    )
    service = DocumentClassifierService(extraction_service=extractor)
    file_path = Path("data/sample_claims/scanned_police_report.png")
    file_path.touch()

    result = service.classify(file_path=str(file_path))
    assert result == DocumentType.POLICE_REPORT


def test_classify_scanned_repair_estimate_image():
    extractor = FakeExtractionService(
        ocr_text="""
        Accident Repair Estimate
        Repair Cost: INR 45,000
        Labor Charges: INR 8,000
        Vehicle Reg: TS09AB1234
        """
    )
    service = DocumentClassifierService(extraction_service=extractor)
    file_path = Path("data/sample_claims/scanned_repair_bill.jpg")
    file_path.touch()

    result = service.classify(file_path=str(file_path))
    assert result == DocumentType.REPAIR_ESTIMATE


def test_classify_scanned_policy_image():
    extractor = FakeExtractionService(
        ocr_text="""
        Motor Insurance Policy
        Policy Number: POL-7788
        Policy Period: 2026-01-01 to 2026-12-31
        Premium: INR 18,000
        Coverage: Comprehensive
        """
    )
    service = DocumentClassifierService(extraction_service=extractor)
    file_path = Path("data/sample_claims/scanned_policy.jpeg")
    file_path.touch()

    result = service.classify(file_path=str(file_path))
    assert result == DocumentType.POLICY


def test_classify_damage_photo_with_non_document_ocr():
    extractor = FakeExtractionService(
        ocr_text="TOYOTA COROLLA SPEED LIMIT 40 FRONT BUMPER"
    )
    service = DocumentClassifierService(extraction_service=extractor)
    file_path = Path("data/sample_claims/car_damage.png")
    file_path.touch()

    # Non-document keywords should classify as DAMAGE_PHOTO
    result = service.classify(file_path=str(file_path))
    assert result == DocumentType.DAMAGE_PHOTO


def test_classify_hindi_police_report():
    service = DocumentClassifierService()
    file_path = Path("data/sample_claims/test_police_report.pdf")
    hindi_text = """
    प्रथम सूचना रिपोर्ट (प्राथमिकी)
    पुलिस स्टेशन: हज़रतगंज, लखनऊ
    घटना की तारीख: २०२६-०९-०५
    """
    result = service.classify(file_path=str(file_path), text=hindi_text)
    assert result == DocumentType.POLICE_REPORT


def test_classify_hindi_repair_estimate():
    service = DocumentClassifierService()
    file_path = Path("data/sample_claims/test_repair_estimate.pdf")
    hindi_text = """
    वाहन मरम्मत अनुमान
    मरम्मत लागत: ₹८५,०००
    श्रम शुल्क: ₹१५,०००
    """
    result = service.classify(file_path=str(file_path), text=hindi_text)
    assert result == DocumentType.REPAIR_ESTIMATE


def test_classify_telugu_claim_form():
    service = DocumentClassifierService()
    file_path = Path("data/sample_claims/test_claim_form.pdf")
    telugu_text = """
    భీమా క్లెయిమ్ ఫారమ్
    క్లెయిమ్ ఐడి: CLM-001
    ప్రమాదం తేదీ: 2026-09-05
    """
    result = service.classify(file_path=str(file_path), text=telugu_text)
    assert result == DocumentType.CLAIM_FORM


def test_classify_tamil_medical_bill():
    service = DocumentClassifierService()
    file_path = Path("data/sample_claims/test_medical_bill.pdf")
    tamil_text = """
    மருத்துவமனை பில்
    நோயாளி: சுரேஷ் குமார்
    மொத்த தொகை: ₹45,000
    """
    result = service.classify(file_path=str(file_path), text=tamil_text)
    assert result == DocumentType.MEDICAL_BILL


def test_classify_hindi_policy():
    service = DocumentClassifierService()
    file_path = Path("data/sample_claims/test_policy.pdf")
    hindi_text = """
    मोटर बीमा पॉलिसी
    पॉलिसी संख्या: POL-2026-001
    पॉलिसी अवधि: 2026-01-01 से 2026-12-31
    प्रीमियम: ₹25,000
    """
    result = service.classify(file_path=str(file_path), text=hindi_text)
    assert result == DocumentType.POLICY
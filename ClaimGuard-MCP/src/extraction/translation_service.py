import json
import logging
import re
from typing import Any

from src.extraction.llm_extraction_service import LLMExtractionService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Indic Numeral Normalization Table
# ---------------------------------------------------------------------------
INDIC_DIGITS_MAP: dict[str, str] = {
    # Devanagari (Hindi, Marathi, Sanskrit, Nepali)
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
    # Telugu
    "౦": "0", "౧": "1", "౨": "2", "౩": "3", "౪": "4",
    "౫": "5", "౬": "6", "౭": "7", "౮": "8", "౯": "9",
    # Tamil
    "௦": "0", "௧": "1", "௨": "2", "௩": "3", "௪": "4",
    "௫": "5", "௬": "6", "௭": "7", "௮": "8", "௯": "9",
    # Bengali / Assamese
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
    # Gujarati
    "૦": "0", "૧": "1", "૨": "2", "૩": "3", "૪": "4",
    "૫": "5", "૬": "6", "૭": "7", "૮": "8", "૯": "9",
    # Kannada
    "೦": "0", "೧": "1", "೨": "2", "೩": "3", "೪": "4",
    "೫": "5", "೬": "6", "೭": "7", "೮": "8", "೯": "9",
    # Malayalam
    "൦": "0", "൧": "1", "൨": "2", "൩": "3", "൪": "4",
    "൫": "5", "൬": "6", "൭": "7", "൮": "8", "൯": "9",
    # Gurmukhi (Punjabi)
    "੦": "0", "੧": "1", "੨": "2", "੩": "3", "੪": "4",
    "੫": "5", "੬": "6", "੭": "7", "੮": "8", "੯": "9",
    # Odia
    "୦": "0", "୧": "1", "୨": "2", "୩": "3", "୪": "4",
    "୫": "5", "୬": "6", "୭": "7", "୮": "8", "୯": "9",
}

# Compiled regex for any Indic numeral
INDIC_DIGITS_REGEX = re.compile("|".join(re.escape(k) for k in INDIC_DIGITS_MAP.keys()))

# Unicode blocks for Indic and regional scripts:
# Devanagari: 0900-097F, Bengali: 0980-09FF, Gurmukhi: 0A00-0A7F,
# Gujarati: 0A80-0AFF, Oriya: 0B00-0B7F, Tamil: 0B80-0BFF,
# Telugu: 0C00-0C7F, Kannada: 0C80-0CFF, Malayalam: 0D00-0D7F, Arabic/Urdu: 0600-06FF
INDIC_SCRIPT_REGEX = re.compile(
    r"[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F"
    r"\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u0600-\u06FF]"
)

# ---------------------------------------------------------------------------
# Dictionary for Common Insurance & Entity Terms in Indian Languages
# ---------------------------------------------------------------------------
COMMON_INDIC_TERMS: dict[str, str] = {
    # Proper Names (Hindi / Devanagari)
    "राहुल": "Rahul",
    "शर्मा": "Sharma",
    "अमित": "Amit",
    "कुमार": "Kumar",
    "सुरेश": "Suresh",
    "राजेश": "Rajesh",
    "वर्मा": "Verma",
    "पटेल": "Patel",
    "सिंह": "Singh",
    "गुप्ता": "Gupta",
    "यादव": "Yadav",
    "रेड्डी": "Reddy",
    "राव": "Rao",
    "नायर": "Nair",
    "मिश्रा": "Mishra",
    "जोशी": "Joshi",
    "पाटिल": "Patil",
    "देशमुख": "Deshmukh",
    "चौधरी": "Chaudhary",
    "अग्रवाल": "Agarwal",
    # Proper Names (Tamil)
    "சுரேஷ்": "Suresh",
    "குமார்": "Kumar",
    "செல்வம்": "Selvam",
    "முருகன்": "Murugan",
    "ரவி": "Ravi",
    # Proper Names (Telugu)
    "వెంకట్": "Venkat",
    "కృష్ణ": "Krishna",
    "శ్రీనివాస్": "Srinivas",
    # Indian Cities
    "हैदराबाद": "Hyderabad",
    "मुंबई": "Mumbai",
    "दिल्ली": "Delhi",
    "बेंगलुरु": "Bengaluru",
    "चेन्नई": "Chennai",
    "कोलकाता": "Kolkata",
    "पुणे": "Pune",
    "जयपुर": "Jaipur",
    "अहमदाबाद": "Ahmedabad",
    "लखनऊ": "Lucknow",
    # Vehicle & Incident Terms (Hindi)
    "कार": "car",
    "ट्रक": "truck",
    "बस": "bus",
    "मोटरसाइकिल": "motorcycle",
    "स्कूटर": "scooter",
    "दुर्घटना": "accident",
    "टक्कर": "collision",
    "चोट": "injury",
    "क्षतिग्रस्त": "damaged",
    "क्षति": "damage",
    "सामने": "front",
    "पीछे": "rear",
    "बाएं": "left",
    "दाएं": "right",
    "बम्पर": "bumper",
    "हेडलाइट": "headlight",
    "दरवाजा": "door",
    "बोनट": "bonnet",
    "पहिया": "wheel",
    "मरम्मत": "repair",
    "लागत": "cost",
    "श्रम": "labor",
    "शुल्क": "charges",
    "अस्पताल": "hospital",
    "मरीज": "patient",
    "रोगी": "patient",
    "पॉलिसी": "policy",
    "बीमा": "insurance",
    "दावा": "claim",
    "प्रथम सूचना रिपोर्ट": "First Information Report",
    "प्राथमिकी": "FIR",
    "पुलिस स्टेशन": "Police Station",
    "थाना": "Police Station",
    "पंजीकरण": "registration",
    "व्यापक": "comprehensive",
    "तृतीय पक्ष": "third party",
    # State Codes in Devanagari (for license plates)
    "एमएच": "MH",
    "डीएल": "DL",
    "यूपी": "UP",
    "टीएस": "TS",
    "एपी": "AP",
    "केए": "KA",
    "टीएन": "TN",
    "जीजे": "GJ",
    "आरजे": "RJ",
    "एमपी": "MP",
    "एचआर": "HR",
    "पीबी": "PB",
    "एबी": "AB",
    "सीडी": "CD",
    # Vehicle & Incident Terms (Tamil)
    "விபத்து": "accident",
    "மோதல்": "collision",
    "சேதம்": "damage",
    "பழுதுபார்ப்பு": "repair",
    "மருத்துவமனை": "hospital",
    "காவல் நிலையம்": "Police Station",
    "பாலிசி": "policy",
    "காப்பீடு": "insurance",
    "கோரிக்கை": "claim",
    # Vehicle & Incident Terms (Telugu)
    "ప్రమాదం": "accident",
    "ఢీకొంది": "collision",
    "నష్టం": "damage",
    "మరమ్మతు": "repair",
    "ఆసుపత్రి": "hospital",
    "పోలీస్ స్టేషన్": "Police Station",
    "పాలసీ": "policy",
    "భీమా": "insurance",
    "క్లెయిమ్": "claim",
}

# ---------------------------------------------------------------------------
# Devanagari Phonetic Character Mapping
# ---------------------------------------------------------------------------
DEVANAGARI_CONSONANTS: dict[str, str] = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h", "क्ष": "ksh", "त्र": "tr", "ज्ञ": "gy",
}

DEVANAGARI_VOWELS: dict[str, str] = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
}

DEVANAGARI_MATRAS: dict[str, str] = {
    "ा": "a", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "n", "ँ": "n", "ः": "h",
}

VIRAMA = "्"


class TranslationService:
    """
    Handles translation and transliteration for insurance claim documents
    written in Indian regional languages (Hindi, Tamil, Telugu, Marathi, etc.).

    Provides:
    1. Fast Indic digits normalization (e.g. '२०२६-०९-०५' -> '2026-09-05').
    2. Rule-based transliteration & dictionary for common insurance entities.
    3. Tier-2 LLM translation pipeline for fluent, contextual field translation.
    """

    def __init__(
        self,
        llm_extraction_service: LLMExtractionService | None = None,
    ) -> None:
        self.llm_extraction_service = (
            llm_extraction_service or LLMExtractionService()
        )

    @staticmethod
    def is_non_latin(text: str) -> bool:
        """Check if the string contains any non-Latin / Indic characters."""
        if not text:
            return False
        return bool(INDIC_SCRIPT_REGEX.search(text))

    @staticmethod
    def normalize_indic_digits(text: str) -> str:
        """
        Convert all Indic numerals (Devanagari, Telugu, Tamil, Bengali, etc.)
        to standard ASCII digits (0-9).
        """
        if not text:
            return ""

        def _replace_digit(match: re.Match) -> str:
            return INDIC_DIGITS_MAP.get(match.group(0), match.group(0))

        return INDIC_DIGITS_REGEX.sub(_replace_digit, text)

    def transliterate_devanagari_word(self, word: str) -> str:
        """
        Phonetically transliterate an individual Devanagari word into Latin script.
        """
        if word in COMMON_INDIC_TERMS:
            return COMMON_INDIC_TERMS[word]

        result: list[str] = []
        i = 0
        n = len(word)

        while i < n:
            char = word[i]

            if char in DEVANAGARI_VOWELS:
                result.append(DEVANAGARI_VOWELS[char])
                i += 1
            elif char in DEVANAGARI_CONSONANTS:
                base = DEVANAGARI_CONSONANTS[char]
                # Look ahead for matra or virama
                if i + 1 < n and word[i + 1] in DEVANAGARI_MATRAS:
                    matra = word[i + 1]
                    result.append(base + DEVANAGARI_MATRAS[matra])
                    i += 2
                elif i + 1 < n and word[i + 1] == VIRAMA:
                    result.append(base)
                    i += 2
                else:
                    # In Hindi/Devanagari, inherently has 'a' unless at end of word
                    if i + 1 == n:
                        result.append(base)
                    else:
                        result.append(base + "a")
                    i += 1
            elif char in DEVANAGARI_MATRAS:
                result.append(DEVANAGARI_MATRAS[char])
                i += 1
            else:
                result.append(char)
                i += 1

        res_str = "".join(result)
        return res_str.capitalize() if res_str else word

    def transliterate_text_offline(self, text: str) -> str:
        """
        Rule-based offline translation/transliteration using vocabulary dictionary
        and phonetic Devanagari transliteration.
        """
        if not text:
            return ""

        # First, normalize any Indic numbers
        normalized = self.normalize_indic_digits(text)

        # Check multi-word phrases first
        for phrase, replacement in COMMON_INDIC_TERMS.items():
            if phrase in normalized:
                normalized = normalized.replace(phrase, replacement)

        # Split remaining words and transliterate any Devanagari tokens
        tokens = normalized.split(" ")
        translated_tokens = []
        for token in tokens:
            stripped = token.strip(" ,.:;!?()[]{}'\"")
            if self.is_non_latin(stripped):
                translit = self.transliterate_devanagari_word(stripped)
                # Keep surrounding punctuation
                translated_token = token.replace(stripped, translit)
                translated_tokens.append(translated_token)
            else:
                translated_tokens.append(token)

        return " ".join(translated_tokens)

    def translate_fields_with_llm(
        self,
        fields_to_translate: dict[str, str],
    ) -> dict[str, str]:
        """
        Use Gemini or OpenAI to perform high-accuracy translation and transliteration
        of non-English field values.
        """
        if not self.llm_extraction_service.is_available():
            return {}

        prompt = (
            "You are an expert insurance document translation engine.\n"
            "The following insurance claim field values are in an Indian regional language "
            "(such as Hindi, Tamil, Telugu, Marathi) or contain non-Latin characters:\n\n"
            f"{json.dumps(fields_to_translate, ensure_ascii=False, indent=2)}\n\n"
            "Instructions:\n"
            "1. Transliterate proper names (e.g. claimant_name, driver_name, hospital_name, police_station) "
            "into standard Latin English script (e.g., 'राहुल शर्मा' -> 'Rahul Sharma', 'சுரேஷ் குமார்' -> 'Suresh Kumar').\n"
            "2. Translate incident descriptions or notes into clear, concise English.\n"
            "3. Standardize vehicle registration numbers into Latin characters and digits (e.g., 'एमएच १२ एबी १२३४' -> 'MH 12 AB 1234').\n"
            "4. Return ONLY a valid JSON object mapping each field name to its translated/transliterated English string.\n"
        )

        try:
            if self.llm_extraction_service.provider == "gemini":
                raw_response = self.llm_extraction_service._call_gemini(prompt)
            else:
                raw_response = self.llm_extraction_service._call_openai(prompt)

            data = self.llm_extraction_service._parse_json_response(raw_response)
            if isinstance(data, dict):
                return {str(k): str(v).strip() for k, v in data.items() if v is not None}
        except Exception as exc:
            logger.warning("LLM translation failed, falling back to offline transliteration: %s", exc)

        return {}

    def translate_field(self, field_name: str, field_value: Any) -> Any:
        """Translate or transliterate a single field value if it contains non-Latin characters."""
        if not isinstance(field_value, str) or not field_value.strip():
            return field_value

        # 1. Normalize Indic numerals
        normalized = self.normalize_indic_digits(field_value)

        # If it doesn't contain non-Latin characters, return normalized
        if not self.is_non_latin(normalized):
            return normalized

        # 2. Try LLM if available
        if self.llm_extraction_service.is_available():
            llm_translated = self.translate_fields_with_llm({field_name: normalized})
            if field_name in llm_translated:
                return llm_translated[field_name]

        # 3. Fallback to offline transliterator & dictionary
        return self.transliterate_text_offline(normalized)

    def translate_fields(
        self,
        extracted_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process a dictionary of extracted fields:
        - Normalizes all Indic numerals across all fields.
        - Translates/transliterates any non-English/Indic field values.
        """
        if not extracted_data:
            return {}

        result = dict(extracted_data)

        # Step 1: Normalize Indic numerals across all string fields
        for key, val in result.items():
            if isinstance(val, str):
                result[key] = self.normalize_indic_digits(val)

        # Step 2: Identify non-Latin fields that require translation/transliteration
        non_latin_fields = {
            k: v for k, v in result.items()
            if isinstance(v, str) and self.is_non_latin(v)
        }

        if not non_latin_fields:
            return result

        # Step 3: Attempt bulk LLM translation if available
        llm_results: dict[str, str] = {}
        if self.llm_extraction_service.is_available():
            llm_results = self.translate_fields_with_llm(non_latin_fields)

        # Step 4: Apply LLM results or offline fallback
        for key, raw_val in non_latin_fields.items():
            if key in llm_results and llm_results[key]:
                result[key] = llm_results[key]
            else:
                result[key] = self.transliterate_text_offline(raw_val)

        return result

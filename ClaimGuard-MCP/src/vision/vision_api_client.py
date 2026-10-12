import base64
import logging

import requests
import truststore
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class VisionAPIClient:
    """
    Client used by ClaimGuard-MCP to communicate with
    the remote Qwen2-VL inference server.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # Inject system trust store once at init, not per request.
        try:
            truststore.inject_into_ssl()
        except Exception:
            pass

        # Configure retry strategy for transient failures.
        self.session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )

        self.session.mount(
            "https://",
            HTTPAdapter(max_retries=retries),
        )

        self.session.mount(
            "http://",
            HTTPAdapter(max_retries=retries),
        )

    def analyze_image(self, file_path: str) -> dict:
        """
        Send an image to the remote vision inference API
        and return the structured model response.
        """
        if not self.base_url:
            raise ValueError(
                "Vision API URL is not configured. Set VISION_API_URL in .env "
                "or provide an active inference endpoint."
            )

        with open(file_path, "rb") as image_file:
            image_base64 = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        logger.info(
            "Sending image to vision API: %s",
            file_path,
        )

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = self.session.post(
            f"{self.base_url}/analyze",
            json={
                "image": image_base64,
            },
            headers=headers,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()
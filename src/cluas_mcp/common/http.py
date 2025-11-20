from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import requests


def _raise_for_status(response: requests.Response) -> requests.Response:
    """
    raise retryable exception for transient HTTP issues.
    considers 429 and 5xx status codes retryable.
    """
    if response.status_code == 429 or response.status_code >= 500:
        raise requests.exceptions.RequestException(
            f"Transient HTTP error {response.status_code}"
        )
    return response


@retry(
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
def fetch_with_retry(url: str, headers:dict = None) -> requests.Response:
    """
    fetches a URL with retry logic suitable for academic APIs.

    retries on:
      - connection errors
      - timeouts
      - 5xx responses
      - 429 responses
    """
    response = requests.get(url, timeout=10, headers=headers or {})
    return _raise_for_status(response)

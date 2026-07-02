import time
from typing import Iterator
import requests
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)
from pingest.exception_helper.core import SourceError
from concurrent.futures import ThreadPoolExecutor, as_completed

from pingest.logging_helper.core import get_logger
from pingest.observability import timed

logger = get_logger(__name__)


def should_retry(exception):
    if isinstance(exception, requests.HTTPError):
        status = exception.response.status_code
        return status >= 500

    return True


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    retry=retry_if_exception(should_retry),
)
def _get_page(session: requests.Session, url: str) -> requests.Response:
    while True:
        res = session.get(url)
        if res.status_code == 429:
            wait = int(res.headers.get("Retry-After", 5))
            time.sleep(wait)
            continue
        break
    res.raise_for_status()
    return res


def get_page(session: requests.Session, url: str) -> requests.Response:
    try:
        return _get_page(session=session, url=url)
    except requests.RequestException as exc:
        raise SourceError(f"Failed to fetch {url}") from exc


def fetch_pages_sequential(session: requests.Session, base_url: str) -> Iterator[dict]:
    first = get_page(url=base_url, session=session)
    first_json = first.json()
    total_pages = first_json["total_pages"]
    yield from first_json["records"]
    for i in range(2, total_pages + 1):
        page = get_page(url=f"{base_url}?page={i}", session=session)
        page_json = page.json()
        yield from page_json["records"]


def fetch_pages_threaded(
    session: requests.Session,
    base_url: str,
    total_pages: int,
    max_workers: int = 5,
) -> list[dict]:

    list_urls = [f"{base_url}?page={i}" for i in range(1, total_pages + 1)]
    records = []
    failed_url = []

    with ThreadPoolExecutor(max_workers=max_workers) as executors:
        futures = {executors.submit(get_page, session, url): url for url in list_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                res = future.result()
                res_json = res.json()
                records.extend(res_json["records"])
            except SourceError as exc:
                logger.error("Failed to fetch", extra={"url": url})
                failed_url.append(url)

    return records


@timed
def run_sequential(session, url):
    return list(fetch_pages_sequential(session, url))


@timed
def run_threaded(session, base_url, total_pages, max_workers=5):
    return fetch_pages_threaded(session, base_url, total_pages, max_workers)

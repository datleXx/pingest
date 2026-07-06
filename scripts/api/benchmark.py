import json
import threading
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import time

import requests
from pingest.logging_helper.core import get_logger
from pingest.models import create_one_mock
from pingest.sources.api import run_async, run_sequential, run_threaded

TOTAL_PAGES = 20
RECORDS_PER_PAGE = 100
LATENCY_S = 0.05

logger = get_logger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class _ReqHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(LATENCY_S)
        parsed = urlparse(self.path)
        parsed_query = parse_qs(parsed.query)
        page = parsed_query.get("page", ["1"])[0]
        body = json.dumps(
            {
                "total_pages": TOTAL_PAGES,
                "records": [
                    create_one_mock().model_dump() for _ in range(RECORDS_PER_PAGE)
                ],
                "page": page,
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadedHTTPServer(("127.0.0.1", 0), _ReqHandler)
    port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}/records"

    session = requests.Session()

    logger.info("Start Sequential timer")

    start_seq = time.perf_counter()
    seq_records = run_sequential(session, base_url)
    end_seq = time.perf_counter()
    duration_seq = (end_seq - start_seq) * 1000

    logger.info(
        "Sequential benchmark done",
        extra={"duration_ms": duration_seq},
    )

    logger.info("Start Threaded timer")

    start_threaded = time.perf_counter()
    threaded_records = run_threaded(session, base_url, TOTAL_PAGES, 5)
    end_threaded = time.perf_counter()
    duration_threaded = (end_threaded - start_threaded) * 1000
    logger.info(
        "Threaded benchmark done",
        extra={"duration_ms": duration_threaded},
    )

    logger.info("Start Async timer")

    start_async = time.perf_counter()
    async_records = run_async(base_url)
    end_async = time.perf_counter()
    duration_async = (end_async - start_async) * 1000

    logger.info("Async benchmark done", extra={"duration_ms": duration_async})


if __name__ == "__main__":
    main()

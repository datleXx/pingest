from collections import deque
from threading import Lock
import time

import requests

from pingest.logging_helper.core import get_logger
from pingest.sources.api import get_page

BASE_URL = "https://api.football-data.org/v4"
logger = get_logger(__name__)


class RateLimiter:
    def __init__(self, calls_per_min: int = 10) -> None:
        self._limit = calls_per_min
        self._window = 60.0
        self._timestamps: deque[float] = deque()
        self._lock = Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            out_of_window = now - self._window
            while self._timestamps and self._timestamps[0] <= out_of_window:
                self._timestamps.popleft()

            if len(self._timestamps) >= self._limit:
                wait = self._window - (now - self._timestamps[0])
                if wait > 0:
                    time.sleep(wait)

            self._timestamps.append(time.monotonic())


class SoccerApiClient:
    def __init__(self, api_key: str, calls_per_min: int = 10) -> None:
        self._session = requests.Session()
        self._limiter = RateLimiter(calls_per_min)
        self._session.headers.update({"X-Auth-Token": api_key})

    def _get(self, path: str, params: dict | None = None):
        self._limiter.acquire()
        response = get_page(self._session, BASE_URL + path, params)
        return response.json()

    def get_competitions(self, areas: str | None = None) -> list[dict]:
        params = {}
        if areas:
            params["areas"] = areas
        return self._get("/competitions", params)["competitions"]

    def get_standings(self, competition: str, season: int | None = None) -> list[dict]:
        params = {}
        if season:
            params["season"] = season
        return self._get(f"/competitions/{competition}/standings", params)["standings"]

    def get_scorers(
        self, competition: str, season: int | None = None, limit: int = 50
    ) -> list[dict]:
        params: dict = {"limit": limit}
        if season:
            params["season"] = season
        return self._get(f"/competitions/{competition}/scorers", params)["scorers"]

    def get_competition_matches(
        self,
        competition: str,
        season: int | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        params = {}
        if season:
            params["season"] = season
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._get(f"/competitions/{competition}/matches", params)["matches"]

    def get_competition_teams(
        self, competition: str, season: int | None = None
    ) -> list[dict]:
        params = {}
        if season:
            params["season"] = season
        return self._get(f"/competitions/{competition}/teams", params)["teams"]

    def get_team_matches(
        self,
        team_id: int,
        season: int | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        params: dict = {"limit": limit}
        if season:
            params["season"] = season
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._get(f"/teams/{team_id}/matches", params)["matches"]

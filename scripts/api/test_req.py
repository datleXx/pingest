import requests
from pingest.sources.api import get_page
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    with requests.Session() as session:
        session.headers.update({"X-Auth-Token": os.environ["FOOTBALL_API_KEY"]})
        res = get_page(
            session,
            url="https://api.football-data.org/v4/teams/86/matches?status=SCHEDULED",
        )
        res.raise_for_status()
        res_js = res.json()

        print(res_js)


if __name__ == "__main__":
    main()

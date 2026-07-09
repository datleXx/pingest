from pydantic import BaseModel


class FlatMatch(BaseModel):
    competition_id: int
    competition_name: str
    competition_code: str
    season_id: int
    season_start_year: int
    match_id: int
    utc_date: str
    match_date: str
    status: str
    matchday: int | None
    stage: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    home_score_ft: int | None
    away_score_ft: int | None
    home_score_ht: int | None
    away_score_ht: int | None
    winner: str | None

    @classmethod
    def from_api(cls, raw: dict) -> "FlatMatch":
        return cls(
            competition_id=raw["competition"]["id"],
            competition_name=raw["competition"]["name"],
            competition_code=raw["competition"]["code"],
            season_id=raw["season"]["id"],
            season_start_year=int(raw["season"]["startDate"][:4]),
            match_id=raw["id"],
            utc_date=raw["utcDate"],
            match_date=raw["utcDate"][:10],
            status=raw["status"],
            matchday=raw.get("matchday"),
            stage=raw["stage"],
            home_team_id=raw["homeTeam"]["id"],
            home_team_name=raw["homeTeam"]["name"],
            away_team_id=raw["awayTeam"]["id"],
            away_team_name=raw["awayTeam"]["name"],
            home_score_ft=raw["score"]["fullTime"]["home"],
            away_score_ft=raw["score"]["fullTime"]["away"],
            home_score_ht=raw["score"]["halfTime"]["home"],
            away_score_ht=raw["score"]["halfTime"]["away"],
            winner=raw["score"]["winner"],
        )


class FlatStanding(BaseModel):
    competition_code: str
    season_start_year: int
    stage: str
    type: str
    position: int
    team_id: int
    team_name: str
    played: int
    won: int
    drawn: int
    lost: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: int
    form: str | None

    @classmethod
    def from_api(
        cls,
        row: dict,
        *,
        competition_code: str,
        season_start_year: int,
        stage: str,
        type: str,
    ) -> "FlatStanding":
        return cls(
            competition_code=competition_code,
            season_start_year=season_start_year,
            stage=stage,
            type=type,
            position=row["position"],
            team_id=row["team"]["id"],
            team_name=row["team"]["name"],
            played=row["playedGames"],
            won=row["won"],
            drawn=row["draw"],
            lost=row["lost"],
            points=row["points"],
            goals_for=row["goalsFor"],
            goals_against=row["goalsAgainst"],
            goal_difference=row["goalDifference"],
            form=row.get("form"),
        )


class FlatScorer(BaseModel):
    competition_code: str
    season_start_year: int
    player_id: int
    player_name: str
    nationality: str | None
    team_id: int
    team_name: str
    goals: int
    assists: int | None
    penalties: int | None

    @classmethod
    def from_api(
        cls, raw: dict, *, competition_code: str, season_start_year: int
    ) -> "FlatScorer":
        return cls(
            competition_code=competition_code,
            season_start_year=season_start_year,
            player_id=raw["player"]["id"],
            player_name=raw["player"]["name"],
            nationality=raw["player"].get("nationality"),
            team_id=raw["team"]["id"],
            team_name=raw["team"]["name"],
            goals=raw["goals"],
            assists=raw.get("assists"),
            penalties=raw.get("penalties"),
        )

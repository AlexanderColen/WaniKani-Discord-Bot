from typing import List
from .Level_Progress import LevelProgress


class User:
    def __init__(self, wk_id: str, username: str, profile_url: str, level: int, last_update: str,
                 member_since: str, subscribed: bool, max_level: int, on_vacation_since: str):
        self.id: str = wk_id
        self.username: str = username
        self.profile_url: str = profile_url
        self.level: int = level
        self.last_update: str = last_update
        self.member_since: str = member_since
        self.subscribed: bool = subscribed
        self.max_level: int = max_level
        self.on_vacation_since: str = on_vacation_since
        self.level_progressions: List[LevelProgress] = []

    def __str__(self):
        return f'User: {self.username} - Level: {self.level} - URL: {self.profile_url}'

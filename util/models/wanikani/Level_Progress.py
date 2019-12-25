class LevelProgress:
    def __init__(self, progress_id: int, last_update: str, level: int, passed: bool, unlocked_at: str,
                 started_at: str, passed_at: str, completed_at: str, abandoned_at: str) -> None:
        self.id: int = progress_id
        self.last_update: str = last_update
        self.level: int = level
        self.passed: bool = passed
        self.unlocked_at: str = unlocked_at
        self.started_at: str = started_at
        self.passed_at: str = passed_at
        self.completed_at: str = completed_at
        self.abandoned_at: str = abandoned_at

    def __str__(self) -> str:
        return f'Level: {self.level} - Passed: {self.passed}'

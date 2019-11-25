class LevelProgress:
    def __init__(self, progress_id, last_update, level, passed, unlocked_at,
                 started_at, passed_at, completed_at, abandoned_at):
        self.id = progress_id
        self.last_update = last_update
        self.level = level
        self.passed = passed
        self.unlocked_at = unlocked_at
        self.started_at = started_at
        self.passed_at = passed_at
        self.completed_at = completed_at
        self.abandoned_at = abandoned_at

    def __str__(self):
        return f'Level: {self.level} - Passed: {self.passed}'

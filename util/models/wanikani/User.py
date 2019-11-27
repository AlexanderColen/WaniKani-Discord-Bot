class User:
    def __init__(self, wk_id, username, profile_url, level, last_update,
                 member_since, subscribed, max_level, on_vacation_since):
        self.id = wk_id
        self.username = username
        self.profile_url = profile_url
        self.level = level
        self.last_update = last_update
        self.member_since = member_since
        self.subscribed = subscribed
        self.max_level = max_level
        self.on_vacation_since = on_vacation_since
        self.level_progressions = []

    def __str__(self):
        return f'User: {self.username} - Level: {self.level} - URL: {self.profile_url}'

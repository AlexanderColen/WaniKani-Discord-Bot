class Summary:
    def __init__(self, last_update, available_lessons, available_reviews, upcoming_reviews):
        self.last_update = last_update
        self.available_lessons = available_lessons
        self.available_reviews = available_reviews
        self.upcoming_reviews = upcoming_reviews

    def __str__(self):
        return f'Available lessons: {len(self.available_lessons)}' \
            f' - Available reviews: {len(self.available_reviews)}' \
            f' - Upcoming reviews: {[len(x) for x in self.upcoming_reviews]}'

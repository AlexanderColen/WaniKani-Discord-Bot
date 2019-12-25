from typing import Any, List


class Summary:
    def __init__(self, last_update: str,
                 available_lessons: List[Any],
                 available_reviews: List[Any],
                 upcoming_reviews: List[Any]) -> None:
        self.last_update: str = last_update
        self.available_lessons: List[Any] = available_lessons
        self.available_reviews: List[Any] = available_reviews
        self.upcoming_reviews: List[Any] = upcoming_reviews

    def __str__(self) -> str:
        return f'Available lessons: {len(self.available_lessons)}' \
            f' - Available reviews: {len(self.available_reviews)}' \
            f' - Upcoming reviews: {[len(x) for x in self.upcoming_reviews]}'

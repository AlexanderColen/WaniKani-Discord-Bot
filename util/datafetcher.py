from .models.wanikani.User import User
from .models.wanikani.Summary import Summary
from .database.datastorage import DataStorage
from typing import Any, Dict, List
import json
import requests


class DataFetcher:
    wanikani_users = {}
    _dataStorage = None

    def __init__(self):
        self._dataStorage = DataStorage()

    async def get_wanikani_data(self, user_id: int, resource: str, after_date: str = None, after_id: str = None):
        """
        Fetch a user's WaniKani data via the API from a resource.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        :param resource: The WaniKani API resource that needs to be called.
        :param after_date: Optional argument for specifying since when you want to check the data.
        :param after_id: Optional argument for specifying after which ID you want to fetch all the data.
        :return: The JSON content of the response, otherwise None if the request fails.
        """
        api_token = self._dataStorage.find_api_user(user_id=user_id)['API_KEY']
        api_url_base = 'https://api.wanikani.com/v2/'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(api_token)}
        # Build the URL.
        api_url = f'{api_url_base}{resource}'

        # Adds query parameters to the URL.
        if after_date:
            api_url = f'{api_url}?updated_after={after_date}T00:00:00.000000Z'
        if after_id:
            api_url = f'{api_url}?page_after_id={after_id}'

        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'))
        else:
            return None

    async def fetch_wanikani_user_data(self, user_id: int) -> User:
        """
        Fetch a WaniKani User's data.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        :return: The data as a util.models.User object.
        """
        user_data: Dict[str, Any] = await self.get_wanikani_data(user_id=user_id, resource='user')
        user: User = User(last_update=user_data['data_updated_at'], wk_id=user_data['data']['id'],
                          username=user_data['data']['username'], profile_url=user_data['data']['profile_url'],
                          level=user_data['data']['level'], member_since=user_data['data']['started_at'],
                          subscribed=user_data['data']['subscribed'],
                          subscription_type=user_data['data']['subscription']['type'],
                          max_level=user_data['data']['subscription']['max_level_granted'],
                          on_vacation_since=user_data['data']['current_vacation_started_at'])
        self.wanikani_users[user_id]['USER_DATA'] = user
        return user

    async def fetch_wanikani_user_summary(self, user_id: int) -> Summary:
        """
        Fetch a WaniKani User's Summary.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        :return: The data as a util.models.Summary object.
        """
        summary_data: Dict[str, Any] = await self.get_wanikani_data(user_id=user_id, resource='summary')
        start: int = 0
        available_reviews: List[int] = []
        upcoming_reviews: List[int] = []
        # Check if there are available reviews.
        if summary_data['data_updated_at'] == summary_data['data']['next_reviews_at']:
            start = 1
            available_reviews = summary_data['data']['reviews'][0]['subject_ids']
        # Loop over all the available review times and add all of them together.
        for i in range(start, len(summary_data['data']['reviews'])):
            upcoming_reviews.extend(summary_data['data']['reviews'][i]['subject_ids'])

        summary: Summary = Summary(last_update=summary_data['data_updated_at'],
                                   available_lessons=summary_data['data']['lessons'][0]['subject_ids'],
                                   available_reviews=available_reviews,
                                   upcoming_reviews=upcoming_reviews)
        self.wanikani_users[user_id]['SUMMARY'] = summary
        return summary

    async def fetch_wanikani_item_counts(self, user_id: int) -> List[int]:
        radicals: int = 0
        kanji: int = 0
        vocabulary: int = 0
        burned: int = 0

        assignments_data: Dict[str, Any] = await self.get_wanikani_data(user_id=user_id, resource='assignments')
        while True:
            # Count every entry.
            for entry in assignments_data['data']:
                if entry['data']['subject_type'] == 'radical':
                    radicals += 1
                elif entry['data']['subject_type'] == 'kanji':
                    kanji += 1
                elif entry['data']['subject_type'] == 'vocabulary':
                    vocabulary += 1

                if entry['data']['srs_stage_name'] == 'Burned':
                    burned += 1

            # Break if there is no more data after this.
            if not assignments_data['pages']['next_url']:
                break
            else:
                after_id = assignments_data['pages']['next_url'][assignments_data['pages']['next_url'].index('page_after_id='):]
                after_id = after_id.replace('page_after_id=', '')
                assignments_data = await self.get_wanikani_data(user_id=user_id,
                                                                resource='assignments',
                                                                after_id=after_id)

        return [radicals, kanji, vocabulary, burned]

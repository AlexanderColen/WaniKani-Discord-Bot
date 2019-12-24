from .models.wanikani.User import User
from .models.wanikani.Summary import Summary
import json
import requests


class DataFetcher:
    wanikani_users = {}

    async def get_wanikani_data(self, user_id, resource, after_date=None):
        """
        Fetch a user's WaniKani data via the API from a resource.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        :param resource: The WaniKani API resource that needs to be called.
        :param after_date: Optional argument for specifying since when you want to check the data.
        :return: The JSON content of the response, otherwise None if the request fails.
        """
        api_token = self.wanikani_users[user_id]['API_KEY']
        api_url_base = 'https://api.wanikani.com/v2/'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(api_token)}
        # Build the URL.
        api_url = f'{api_url_base}{resource}'

        # Adds updated_after query with the date to the URL.
        if after_date:
            api_url = f'{api_url}?updated_after={after_date}T00:00:00.000000Z'

        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'))
        else:
            return None

    async def fetch_wanikani_user_data(self, user_id):
        """
        Fetch a WaniKani User's data.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        :return: The data as a util.models.User object.
        """
        user_data = await self.get_wanikani_data(user_id=user_id, resource='user')
        user = User(last_update=user_data['data_updated_at'], wk_id=user_data['data']['id'],
                    username=user_data['data']['username'], profile_url=user_data['data']['profile_url'],
                    level=user_data['data']['level'], member_since=user_data['data']['started_at'],
                    subscribed=user_data['data']['subscribed'],
                    max_level=user_data['data']['subscription']['max_level_granted'],
                    on_vacation_since=user_data['data']['current_vacation_started_at'])
        self.wanikani_users[user_id]['USER_DATA'] = user
        return user

    async def fetch_wanikani_user_summary(self, user_id):
        """
        Fetch a WaniKani User's Summary.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        :return: The data as a util.models.Summary object.
        """
        summary_data = await self.get_wanikani_data(user_id=user_id, resource='summary')
        start = 0
        available_reviews = []
        upcoming_reviews = []
        # Check if there are available reviews.
        if summary_data['data_updated_at'] == summary_data['data']['next_reviews_at']:
            start = 1
            available_reviews = summary_data['data']['reviews'][0]['subject_ids']
        # Loop over all the available review times and add all of them together.
        for i in range(start, len(summary_data['data']['reviews'])):
            upcoming_reviews.extend(summary_data['data']['reviews'][i]['subject_ids'])\

        summary = Summary(last_update=summary_data['data_updated_at'],
                          available_lessons=summary_data['data']['lessons'][0]['subject_ids'],
                          available_reviews=available_reviews,
                          upcoming_reviews=upcoming_reviews)
        self.wanikani_users[user_id]['SUMMARY'] = summary
        return summary

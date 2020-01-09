from pymongo import MongoClient, errors
from typing import Dict, Any


class DataStorage:
    client: MongoClient = None
    db = None

    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client['wanikani-bot']

    def register_api_user(self, user_id: int, api_key: str) -> None:
        """
        Inserts a new WaniKani user with their API key into the database.
        :param user_id: The Discord Member ID.
        :param api_key: The API key to access WaniKani's API.
        """
        users = self.db['wanikani-users']
        users.update_one({"_id": user_id}, {"$set": {"API_KEY": api_key}}, True)

    def find_api_user(self, user_id: int) -> Dict[str, Any]:
        """
        Gets a WaniKani user based on ID.
        :param user_id: The Discord Member ID.
        :return: The first found WaniKani user object.
        """
        users = self.db['wanikani-users']
        return users.find_one({"_id": user_id})

    def remove_api_user(self, user_id: int) -> int:
        """
        Deletes a WaniKani user based on ID.
        :param user_id: The Discord Member ID.
        :return: The amount of deleted objects.
        """
        users = self.db['wanikani-users']
        return users.delete_one({"_id": user_id}).deleted_count

    def insert_guild_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Inserts a new Discord Guild with their prefix into the database.
        :param guild_id: The Discord Guild ID.
        :param prefix: The custom prefix.
        """
        prefixes = self.db['guild-prefixes']
        prefixes.update_one({"_id": guild_id}, {"$set": {"prefix": prefix}}, True)

    def find_guild_prefix(self, guild_id: int) -> Dict[str, Any]:
        """
        Gets a custom prefix for a Discord Guild based on ID.
        :param guild_id: The Discord Guild ID.
        :return: The first found prefix.
        """
        prefixes = self.db['guild-prefixes']
        return prefixes.find_one({"_id": guild_id})

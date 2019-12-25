from client import WaniKaniBotClient
from discord.errors import LoginFailure
from typing import Any, Dict
import json


if __name__ == '__main__':
    print('WaniKani Discord Bot - Copyright (C) 2019 - Alexander Colen')
    token: str = None
    print('Fetching settings.json...')
    with open('resources/settings.json') as json_data_file:
        data: Dict[str, Any] = json.load(json_data_file)
        if data["CRABIGATOR_VERSION"]:
            print(f'Running Crabigator Bot v{data["CRABIGATOR_VERSION"]}')

        if data["DISCORD_BOT_TOKEN"]:
            token: str = data["DISCORD_BOT_TOKEN"]
        else:
            print("Settings.json is corrupt. Please redownload the original file to fix this.")

    print('Starting WaniKaniClient...')
    client: WaniKaniBotClient = WaniKaniBotClient()
    try:
        if token != "EMPTY":
            client.run(token)
        else:
            print("Did you forget to enter your Discord bot token in settings.json?")
    except LoginFailure:
        print('Fetched token was invalid. Please make sure that you edited settings.json correctly.')

    noToken: bool = True
    while noToken:
        token = input('Enter Discord Bot token:\n>>>')
        print('Attempting to login...')
        # Exit application if user prompts to.
        if token.lower() in ['quit', 'exit', 'q']:
            break

        try:
            client.run(token)
        except LoginFailure:
            print('Token was invalid. Please try again or type "exit" to quit')

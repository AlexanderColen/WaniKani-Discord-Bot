from models.wanikani.User import User
from models.wanikani.Summary import Summary
from datetime import datetime
import discord
import json
import random
import requests


class WaniKaniBotClient(discord.Client):
    prefix = 'wk!'
    sayings = []
    wanikani_users = {}

    # Fetch a user's WaniKani data via the API from a resource.
    async def get_wanikani_data(self, user_id, resource):
        api_token = self.wanikani_users[user_id]['API_KEY']
        api_url_base = 'https://api.wanikani.com/v2/'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(api_token)}
        api_url = '{0}{1}'.format(api_url_base, resource)
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'))
        else:
            return None

    # Fetch a WaniKani User's data.
    async def fetch_wanikani_user_data(self, user_id):
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

    # Send an image to a channel.
    @staticmethod
    async def send_image(channel, image_name, recipient=''):
        content = ''
        if recipient.startswith('<@'):
            content = recipient
        with open(image_name, 'rb') as image:
            await channel.send(content=content, file=discord.File(fp=image, filename=image_name))

    # Send an embedded message to a channel.
    async def send_embed(self, channel, embed, contains_description=False, contains_footer=False):
        # Add a random description if it is empty.
        if not contains_description and len(self.sayings) > 0:
            embed.description = f'_{self.sayings[random.randint(0, len(self.sayings) - 1)]}_'

        if not contains_footer and embed.author.name == self.user.display_name:
            embed.set_footer(text=f'Click on {self.user.display_name} at the top to check me out on GitHub!',
                             icon_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png')

        await channel.send(embed=embed)

    # Generic error message.
    async def oopsie(self, channel, attempted_command):
        await channel.send(
            content=f'Crabigator got too caught up studying and failed to handle `{self.prefix}{attempted_command}`. '
            f'Please try again.')

    # Handle requests (commands) given to the Crabigator.
    async def handle_command(self, message):
        words = message.content.split(' ')
        command = words[0].lower()

        # Changes the prefix for the almighty Crabigator.
        if command == 'prefix':
            if len(words) == 1:
                await message.channel.send(
                    content=f"Don't treat the prefix like your Kanji and forget it! "
                    f'Example usage: `{self.prefix}prefix <CHAR>`')
            elif len(words) > 2:
                await message.channel.send(
                    content=f'The Crabigator does not allow spaces in the prefix!')
            else:
                self.prefix = words[1]
                await message.channel.send(
                    content=f'The Crabigator became more omnipotent by changing to `{self.prefix}`!')
        # Registers a WaniKani User for API calls.
        elif command == 'adduser':
            if len(words) == 1:
                await message.channel.send(
                    content=f'Improper command usage. '
                    f'Example usage: `{self.prefix}wkadduser <WANIKANI_API_V2_TOKEN>`')
            elif len(words[1]) != 36 or '-' not in words[1]:
                await message.channel.send(
                    content='API token is invalid! '
                            'Make sure there are no dangling characters on either side!')
            else:
                self.wanikani_users[message.author.id] = {'API_KEY': words[1]}
                await message.delete()
                await message.channel.send(
                    content=f'Crabigator has started watching <@{message.author.id}> closely...')
        # Deregisters a WaniKani User for API calls.
        elif command == 'removeuser':
            try:
                self.wanikani_users.pop(message.author.id)
                # Find custom emoji if possible.
                emoji = ':sob:'
                for em in await message.guild.fetch_emojis():
                    if any(e in em.name.lower() for e in ['baka', 'pout', 'sad', 'cry']):
                        emoji = f'<:{em.name}:{em.id}>'

                await message.channel.send(
                    content=f"The Cult of the Crabigator didn't want you in the first place. {emoji}")
            except KeyError:
                await message.channel.send(
                    content=f'Crabigator does not know this person. I cannot delete what I do not know. ')
        # Fetch a WaniKani User's overall stats.
        elif command in ['user', 'userstats']:
            if len(words) == 1:
                if message.author.id in self.wanikani_users.keys():
                    user = await self.fetch_wanikani_user_data(user_id=message.author.id)
                    embed = discord.Embed(title='WaniKani Profile', url=user.profile_url,
                                          colour=message.author.colour, timestamp=datetime.now())
                    embed.set_thumbnail(url='https://cdn.wanikani.com/default-avatar-300x300-20121121.png')
                    embed.set_author(name=user.username, icon_url=message.author.avatar_url,
                                     url=user.profile_url)
                    summary = await self.fetch_wanikani_user_summary(user_id=message.author.id)
                    # Add all the custom embed fields.
                    embed.add_field(name='Level', value=user.level, inline=False)
                    embed.add_field(name='Lessons available:', value=len(summary.available_lessons), inline=False)
                    embed.add_field(name='Reviews available:', value=len(summary.available_reviews), inline=False)
                    await self.send_embed(channel=message.channel, embed=embed)
                else:
                    await message.channel.send(
                        content=f'Crabigator does not know this person. '
                        f'Please use `{self.prefix}wkadduser <WANIKANI_API_V2_TOKEN>` and try again.')
        # Fetch a WaniKani User's leveling statistics.
        elif command == 'levelstats':
            if len(words) == 1:
                try:
                    if 'USER_DATA' not in self.wanikani_users[message.author.id]:
                        await self.fetch_wanikani_user_data(user_id=message.author.id)
                    user = self.wanikani_users[message.author.id]['USER_DATA']
                    level_progressions = await self.get_wanikani_data(message.author.id, 'level_progressions')
                    # Add found data to user object.
                    for level_progress in level_progressions['data']:
                        user.level_progressions.append(level_progress)
                    await message.channel.send(
                        content=f"Compiling your data took forever, so I took a nap instead. "
                        f"Just use https://www.wkstats.com/ for now.")
                except KeyError:
                    await message.channel.send(
                        content=f'Crabigator does not know this person. '
                        f'Please use `{self.prefix}wkadduser <WANIKANI_API_V2_TOKEN>` and try again.')
        # Congratulate someone.
        elif command in ['grats', 'gratz', 'congrats', 'congratulations', 'gz', 'gj', 'goodjob']:
            if len(words) == 1:
                await self.send_image(channel=message.channel, image_name='img/concrabs.png')
            else:
                await self.send_image(channel=message.channel, image_name='img/concrabs.png', recipient=words[1])
        # Rage at someone.
        elif command in ['boo', 'anger', 'angry', 'bad', 'rage']:
            if len(words) == 1:
                await self.send_image(channel=message.channel, image_name='img/crabrage.png')
            else:
                await self.send_image(channel=message.channel, image_name='img/crabrage.png', recipient=words[1])
        # Wish someone a Merry Crabmas™.
        elif command in ['love', '<3', 'heart']:
            if len(words) == 1:
                await self.send_image(channel=message.channel, image_name='img/crablove.png')
            else:
                await self.send_image(channel=message.channel, image_name='img/crablove.png', recipient=words[1])
        # Eva.
        elif command in ['eva']:
            await self.send_image(channel=message.channel, image_name='img/eva.png')
        # Clearly the case.
        elif command in ['ballot_box_with_check', ':ballot_box_with_check:', '☑']:
            await self.send_image(channel=message.channel, image_name='img/superior_checkmark.png')
        # Provides help with this Bot's commands.
        elif command == 'help':
            if len(words) == 1:
                embed = discord.Embed(title=f"{self.user.display_name} Commands Help",
                                      colour=self.user.colour, timestamp=datetime(year=2019, month=11, day=24))
                embed.set_thumbnail(url='https://i.imgur.com/Fjk2Dv1.png')
                embed.set_author(name=self.user.display_name, icon_url=self.user.avatar_url,
                                 url='https://github.com/AlexanderColen/WaniKaniDiscordBot')
                # Add all the custom embed fields.
                embed.add_field(name=f'{self.prefix}help',
                                value='Displays this embedded message.',
                                inline=False)
                embed.add_field(name=f'{self.prefix}help `<COMMAND_NAME>`',
                                value='Displays more info for the specified command.',
                                inline=False)
                embed.add_field(name=f'{self.prefix}adduser `<WANIKANI_API_V2_TOKEN>`',
                                value='Registers a WaniKani user to allow API usage.',
                                inline=False)
                embed.add_field(name=f'{self.prefix}removeuser',
                                value="Removes a user's data to no longer allow API usage.",
                                inline=False)
                embed.add_field(name=f'{self.prefix}user',
                                value="Fetches the WaniKani user's overall statistics.",
                                inline=False)
                embed.add_field(name=f'{self.prefix}levelstats',
                                value="Fetches the WaniKani user's leveling statistics.",
                                inline=False)
                embed.add_field(name=f'{self.prefix}congratulations',
                                value=':tada:',
                                inline=True)
                embed.add_field(name=f'{self.prefix}anger',
                                value=':anger:',
                                inline=True)
                embed.add_field(name=f'{self.prefix}love',
                                value=':heart:',
                                inline=True)
                await self.send_embed(channel=message.channel, embed=embed)
            else:
                if words[1] == 'help':
                    await self.send_image(channel=message.channel, image_name='img/yodawg.png')
                else:
                    embed = discord.Embed(title=f"{self.user.display_name}'s `{self.prefix}{words[1]}` Command Assistance",
                                          colour=self.user.colour, timestamp=datetime(year=2019, month=11, day=24))
                    embed.set_thumbnail(url='https://i.imgur.com/Fjk2Dv1.png')
                    embed.set_author(name=self.user.display_name, icon_url=self.user.avatar_url,
                                     url='https://github.com/AlexanderColen/WaniKaniDiscordBot')
                    embed.set_footer(text=f'Click on {self.user.display_name} at the top to check me out on GitHub!',
                                     icon_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png')
                    # Add all the custom embed fields.
                    embed.add_field(name='工事中',
                                    value='鰐 and 蟹 are ignoring their reviews to make this command a reality.',
                                    inline=False)
                    embed.set_image(url='https://i.imgur.com/hTCEbR7.png')
                    await self.send_embed(channel=message.channel, embed=embed)
        # Unknown Command.
        else:
            await message.channel.send(
                content=f'Crabigator has yet to learn this ~~kanji~~ command. '
                f'Refer to `{self.prefix}help` to see what I can do!')

    def load_sayings(self):
        with open('resources/descriptions.txt', 'r', encoding='utf-8') as f:
            for l in f:
                self.sayings.append(l)

    async def on_ready(self):
        version = discord.version_info
        print(f'Running on Discord.py v{version.major}.{version.minor}.{version.micro}-{version.releaselevel}\n')
        print('#################################')
        print('# Logged on as {0}! #'.format(self.user))
        print('#################################')
        await self.change_presence(activity=discord.Game('Learning ALL the Kanji!'), status=discord.Status.online)
        self.load_sayings()

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.content.startswith(self.prefix):
            print('\n{0}'.format(message))
            print('Message in {0.guild} - #{0.channel} from {0.author}: {0.content}'.format(message))
            message.content = message.content.lstrip(self.prefix)
            # Prevent empty commands.
            if message.content:
                async with message.channel.typing():
                    try:
                        await self.handle_command(message=message)
                    except discord.DiscordException as ex:
                        print(ex)
                        await self.oopsie(channel=message.channel, attempted_command=message.content.split(' ')[0])

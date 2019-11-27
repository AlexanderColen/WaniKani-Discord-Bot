from util.asynctimer import Scheduler
from util.datafetcher import DataFetcher
from datetime import datetime
import discord
import random


class WaniKaniBotClient(discord.Client):
    prefix = 'wk!'
    command_count = 0
    descriptions = None
    statuses = None
    _dataFetcher = None
    _scheduler = None

    def __init__(self):
        super(WaniKaniBotClient, self).__init__()
        self._dataFetcher = DataFetcher()
        self._scheduler = Scheduler()
        self.descriptions = self.load_text_from_file_to_array(filename='resources/descriptions.txt')
        self.statuses = self.load_text_from_file_to_array(filename='resources/statuses.txt')

    # Event method that gets called when the connection to Discord has been established.
    async def on_ready(self):
        version = discord.version_info
        print(f'Running on Discord.py v{version.major}.{version.minor}.{version.micro}-{version.releaselevel}\n')
        print('#################################')
        print('# Logged on as {0}! #'.format(self.user))
        print('#################################')
        await self.change_status()
        await self._scheduler.run(coro=self.change_status, time=60)

    # Event method that gets called when the Discord client receives a new message.
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.content.startswith(self.prefix):
            print('\n{0}'.format(message))
            print('Message in {0.guild} - #{0.channel} from {0.author}: {0.content}'.format(message))
            message.content = message.content.lstrip(self.prefix)
            # Prevent empty commands.
            if message.content:
                self.command_count += 1
                async with message.channel.typing():
                    try:
                        await self.handle_command(message=message)
                    except discord.DiscordException as ex:
                        print(ex)
                        await self.oopsie(channel=message.channel, attempted_command=message.content.split(' ')[0])

    # Send an image to a channel.
    @staticmethod
    async def send_image(channel, image_name):
        with open(image_name, 'rb') as image:
            await channel.send(file=discord.File(fp=image, filename=image_name))

    # Send an embedded message to a channel.
    async def send_embed(self, channel, embed, contains_description=False, contains_footer=False):
        # Add a random description if it is empty.
        if not contains_description and len(self.descriptions) > 0:
            embed.description = f'_{random.choice(self.descriptions)}_'

        # Add the GitHub as a footer if it is empty and the author is Crabigator.
        if not contains_footer and embed.author.name == self.user.display_name:
            embed.set_footer(text=f'Click on {self.user.display_name} at the top to check me out on GitHub!',
                             icon_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png')

        await channel.send(embed=embed)

    # Converts every line in a file to an entry in an array.
    @staticmethod
    def load_text_from_file_to_array(filename):
        out = []
        with open(filename, 'r', encoding='utf-8') as f:
            for l in f:
                out.append(l)

        return out

    # Find a custom emoji from a guild containing one of the words in the given array.
    @staticmethod
    async def fetch_emoji(guild, emoji_array):
        for em in await guild.fetch_emojis():
            if any(e in em.name.lower() for e in emoji_array):
                return f'<:{em.name}:{em.id}>'

        return ''

    # Change the status to a random one.
    async def change_status(self):
        await self.change_presence(
            activity=discord.Game(f'{random.choice(self.statuses)}')
        )

        # Unknown WaniKani user error message.
    async def unknown_wanikani_user(self, channel):
        await channel.send(
            content=f'Crabigator does not know this person. '
            f'Please use `{self.prefix}adduser <WANIKANI_API_V2_TOKEN>` and try again.')

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
        if command in ['prefix']:
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
        elif command in ['adduser', 'addme']:
            if len(words) == 1:
                await message.channel.send(
                    content=f'Improper command usage. '
                    f'Example usage: `{self.prefix}adduser <WANIKANI_API_V2_TOKEN>`')
            elif len(words[1]) != 36 or '-' not in words[1]:
                await message.channel.send(
                    content='API token is invalid! '
                            'Make sure there are no dangling characters on either side!')
            else:
                self._dataFetcher.wanikani_users[message.author.id] = {'API_KEY': words[1]}
                await message.delete()
                await message.channel.send(
                    content=f'Crabigator has started watching <@{message.author.id}> closely...')
        # Deregisters a WaniKani User for API calls.
        elif command in ['removeuser', 'removeme']:
            try:
                self._dataFetcher.wanikani_users.pop(message.author.id)
                emoji = await self.fetch_emoji(guild=message.guild, emoji_array=['baka', 'pout', 'sad', 'cry'])

                await message.channel.send(
                    content=f"The Cult of the Crabigator didn't want you in the first place. {emoji}")
            except KeyError:
                emoji = await self.fetch_emoji(guild=message.guild, emoji_array=['thinking'])

                await message.channel.send(
                    content=f'Crabigator does not know this person. I cannot delete what I do not know. {emoji}')
        # Fetch a WaniKani User's overall stats.
        elif command in ['user', 'userstats']:
            await self.get_user_stats(words=words, channel=message.channel, author=message.author)
        # Fetch a WaniKani User's daily stats.
        elif command in ['daily', 'dailyoverview', 'dailystatus', 'dailystats']:
            await self.get_daily_stats(words=words, channel=message.channel, author=message.author)
        # Fetch a WaniKani User's leveling statistics.
        elif command in ['levelstats', 'levelstats', 'leveling', 'levelingstatus', 'levelingstats']:
            await self.get_leveling_stats(words=words, channel=message.channel, author=message.author)
        # Congratulate someone.
        elif command in ['congratulations', 'congrats', 'grats', 'gratz', 'gz', 'gj', 'goodjob']:
            await self.send_image(channel=message.channel, image_name='img/concrabs.png')
        # Rage at someone.
        elif command in ['boo', 'anger', 'angry', 'bad', 'rage']:
            await self.send_image(channel=message.channel, image_name='img/crabrage.png')
        # Wish someone a Merry Crabmas™.
        elif command in ['love', '<3', 'heart']:
            await self.send_image(channel=message.channel, image_name='img/crablove.png')
        # Eva.
        elif command in ['eva']:
            await self.send_image(channel=message.channel, image_name='img/eva.png')
        # Clearly the case.
        elif command in ['ballot_box_with_check', ':ballot_box_with_check:', '☑']:
            await self.send_image(channel=message.channel, image_name='img/superior_checkmark.png')
        # Provides help with this Bot's commands.
        elif command in ['help']:
            await self.get_help(words=words, channel=message.channel)
        # Unknown Command.
        else:
            await message.channel.send(
                content=f'Crabigator has yet to learn this ~~kanji~~ command. '
                f'Refer to `{self.prefix}help` to see what I can do!')

    # Get the user_data field from the DataFetcher as a User object.
    async def get_user_data_model(self, user_id):
        if 'USER_DATA' not in self._dataFetcher.wanikani_users[user_id]:
            await self._dataFetcher.fetch_wanikani_user_data(user_id=user_id)
        return self._dataFetcher.wanikani_users[user_id]['USER_DATA']

    # Fetches and displays a WaniKani user.
    async def get_user_stats(self, words, channel, author):
        if len(words) == 1:
            if author.id in self._dataFetcher.wanikani_users.keys():
                user = await self._dataFetcher.fetch_wanikani_user_data(user_id=author.id)
                embed = discord.Embed(title='WaniKani Profile', url=user.profile_url,
                                      colour=author.colour, timestamp=datetime.now())
                embed.set_thumbnail(url='https://cdn.wanikani.com/default-avatar-300x300-20121121.png')
                embed.set_author(name=user.username, icon_url=author.avatar_url,
                                 url=user.profile_url)
                summary = await self._dataFetcher.fetch_wanikani_user_summary(user_id=author.id)
                # Add all the custom embed fields.
                embed.add_field(name='Level', value=user.level, inline=False)
                embed.add_field(name='Lessons available:', value=str(len(summary.available_lessons)), inline=False)
                embed.add_field(name='Reviews available:', value=str(len(summary.available_reviews)), inline=False)
                await self.send_embed(channel=channel, embed=embed)
            else:
                await self.unknown_wanikani_user(channel=channel)

    # Fetches and displays daily statistics for a WaniKani user.
    async def get_daily_stats(self, words, channel, author):
        if len(words) == 1:
            try:
                user = await self.get_user_data_model(user_id=author.id)
                date = datetime.today().strftime('%Y-%m-%d')
                completed_lessons_data = await self._dataFetcher.get_wanikani_data(user_id=author.id,
                                                                                   resource='assignments',
                                                                                   after_date=date)
                completed_reviews_data = await self._dataFetcher.get_wanikani_data(user_id=author.id,
                                                                                   resource='reviews',
                                                                                   after_date=date)
                summary_data = await self._dataFetcher.fetch_wanikani_user_summary(user_id=author.id)
                embed = discord.Embed(title='Daily Overview',
                                      colour=author.colour, timestamp=datetime.now())
                embed.set_thumbnail(url='https://cdn.wanikani.com/default-avatar-300x300-20121121.png')
                embed.set_author(name=user.username, icon_url=author.avatar_url,
                                 url=user.profile_url)
                # Add all the custom embed fields.
                embed.add_field(name='Completed Reviews',
                                value=completed_reviews_data['total_count'],
                                inline=False)
                embed.add_field(name='Completed Lessons',
                                value=completed_lessons_data['total_count'],
                                inline=False)
                embed.add_field(name='Reviews available:',
                                value=str(len(summary_data.available_reviews)),
                                inline=False)
                embed.add_field(name='Lessons available:',
                                value=str(len(summary_data.available_lessons)),
                                inline=False)
                await self.send_embed(channel=channel, embed=embed)
            except KeyError:
                await self.unknown_wanikani_user(channel=channel)

    # Fetches and displays leveling statistics for a WaniKani user.
    async def get_leveling_stats(self, words, channel, author):
        if len(words) == 1:
            try:
                user = await self.get_user_data_model(user_id=author.id)
                level_progressions = await self._dataFetcher.get_wanikani_data(user_id=author.id,
                                                                               resource='level_progressions')
                # Add found data to user object.
                for level_progress in level_progressions['data']:
                    user.level_progressions.append(level_progress)
                await channel.send(
                    content=f"Compiling your data took forever, so I took a nap instead. "
                    f"Just use https://www.wkstats.com/ for now.")
            except KeyError:
                await self.unknown_wanikani_user(channel=channel)

    # Display help for the usage of the bot.
    async def get_help(self, words, channel):
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
                            value="Displays the WaniKani user's overall statistics.",
                            inline=False)
            embed.add_field(name=f'{self.prefix}levelstats',
                            value="Displays the WaniKani user's leveling statistics.",
                            inline=False)
            embed.add_field(name=f'{self.prefix}daily',
                            value="Displays the WaniKani user's daily statistics.",
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
            await self.send_embed(channel=channel, embed=embed)
        else:
            if words[1] == 'help':
                await self.send_image(channel=channel, image_name='img/yodawg.png')
            else:
                embed = discord.Embed(title=f"{self.user.display_name}'s `{self.prefix}{words[1]}` Command Assistance",
                                      colour=self.user.colour, timestamp=datetime(year=2019, month=11, day=24))
                embed.set_thumbnail(url='https://i.imgur.com/Fjk2Dv1.png')
                embed.set_author(name=self.user.display_name, icon_url=self.user.avatar_url,
                                 url='https://github.com/AlexanderColen/WaniKaniDiscordBot')
                embed.set_footer(text=f'Click on {self.user.display_name} at the top to check me out on GitHub!',
                                 icon_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png')
                # Add all the custom embed fields.
                embed.add_field(name='**工事中 - UNDER CONSTRUCTION**',
                                value='鰐 and 蟹 are ignoring their reviews to make this command a reality.',
                                inline=False)
                embed.set_image(url='https://i.imgur.com/hTCEbR7.png')
                await self.send_embed(channel=channel, embed=embed)

from util.asynctimer import Scheduler
from util.database.datastorage import DataStorage
from util.datafetcher import DataFetcher
from util.models.wanikani.Level_Progress import LevelProgress
from util.models.wanikani.Summary import Summary
from util.models.wanikani.User import User
from datetime import datetime
from PIL import Image, ImageFont, ImageDraw
from typing import Any, Dict, List
import discord
import random


class WaniKaniBotClient(discord.Client):
    command_count: int = 0
    descriptions: List[str] = None
    statuses: List[str] = None
    _dataFetcher: DataFetcher = None
    _dataStorage: DataStorage = None
    _scheduler: Scheduler = None

    def __init__(self) -> None:
        super(WaniKaniBotClient, self).__init__()
        self._dataFetcher = DataFetcher()
        self._dataStorage = DataStorage()
        self._scheduler = Scheduler()
        self.descriptions = self.load_text_from_file_to_array(filename='resources/descriptions.txt')
        self.statuses = self.load_text_from_file_to_array(filename='resources/statuses.txt')

    async def on_ready(self) -> None:
        """
        Event method that gets called when the connection to Discord has been established.
        """
        version: discord.VersionInfo = discord.version_info
        print(f'Running on Discord.py v{version.major}.{version.minor}.{version.micro}-{version.releaselevel}\n')
        print('#################################')
        print('# Logged on as {0}! #'.format(self.user))
        print('#################################')
        await self.change_status()
        await self._scheduler.run(coro=self.change_status, time=60)

    async def on_message(self, message: discord.Message) -> None:
        """
        Event method that gets called when the Discord client receives a new message.
        :param message: The Discord.Message that was received.
        """
        # Ignore messages from bots.
        if message.author.bot:
            return

        # Find the appropriate prefix for a server.
        prefix: str = 'wk!'
        if message.guild:
            found_guild = self._dataStorage.find_guild_prefix(guild_id=message.guild.id)
            if found_guild:
                prefix = found_guild['prefix']

        #############################
        # UNCOMMENT FOR MAINTENANCE #
        #############################
        """
        # Replace the ID to your Discord User ID to allow access only for you.
        if message.author.id != 209076181365030913 and message.content.startswith(prefix):
            await message.channel.send(
                content='Crabigator is being operated on. '
                        'Please try again later or contact the Lord of All <@!209076181365030913>.')
            return
        """

        if message.content.startswith(prefix):
            print('\n{0}'.format(message))
            print('Message in {0.guild} - #{0.channel} from {0.author}: {0.content}'.format(message))
            message.content = message.content[len(prefix):]
            # Prevent empty commands.
            if message.content:
                self.command_count += 1
                await message.channel.trigger_typing()
                try:
                    await self.handle_command(message=message, prefix=prefix)
                except Exception as ex:
                    print(ex)
                    await self.oopsie(channel=message.channel,
                                      attempted_command=message.content.split(' ')[0],
                                      prefix=prefix)

    @staticmethod
    async def send_image(channel: discord.TextChannel, image_name: str) -> None:
        """
        Send an image to a channel.
        :param channel: A Discord.TextChannel object to send the image to.
        :param image_name: The local name of the image.
        """
        with open(image_name, 'rb') as image:
            await channel.send(file=discord.File(fp=image, filename=image_name))

    async def send_embed(self, channel: discord.TextChannel, embed: discord.Embed,
                         contains_description: bool = False, contains_footer: bool = False) -> None:
        """
        Send a Discord.Embed to a Discord.TextChannel. Adds a description and footer if none are attached.
        :param channel: The Discord.TextChannel that the message should be sent to.
        :param embed: The Discord.Embed object that should be sent.
        :param contains_description: Boolean indicating whether the embed contains a description.
        :param contains_footer: Boolean indicating whether the embed contains a footer.
        """
        # Add a random description if it is empty.
        if not contains_description and len(self.descriptions) > 0:
            embed.description: str = f'_{random.choice(self.descriptions)}_'

        # Add the GitHub as a footer if it is empty and the author is Crabigator.
        if not contains_footer and embed.author.name == self.user.display_name:
            embed.set_footer(text=f'Click on {self.user.display_name} at the top to check me out on GitHub!',
                             icon_url='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png')

        await channel.send(embed=embed)

    @staticmethod
    def load_text_from_file_to_array(filename: str) -> List[str]:
        """
        Converts every line in a file to an entry in an array. Makes sure that utf-8 encoding is used.
        :param filename: The name of the local file.
        :return: An array containing all the sentences.
        """
        out: List[str] = []
        with open(filename, 'r', encoding='utf-8') as f:
            for l in f:
                out.append(l)

        return out

    @staticmethod
    async def fetch_emoji(guild: discord.Guild, emoji_array: List[str]) -> str:
        """
        Find a custom emoji from a Discord.Guild containing one of the words in the given array.
        :param guild: The Discord.Guild that should be searched. Can be None.
        :param emoji_array: The array of words that should be searched for.
        :return: The first hit from the emoji_array properly formatted to be sent. Empty string if nothing was found.
        """
        if guild:
            # Shuffle emoji array to mix up the potential results.
            random.shuffle(emoji_array)
            for em in await guild.fetch_emojis():
                if any(e in em.name.lower() for e in emoji_array):
                    return f'<:{em.name}:{em.id}>'

        return ''

    async def change_status(self) -> None:
        """
        Changes the status of the Crabigator to a random sentence from resources.statuses.txt.
        """
        await self.change_presence(
            activity=discord.Game(f'{random.choice(self.statuses)}')
        )

    @staticmethod
    async def unknown_wanikani_user(channel: discord.TextChannel, prefix: str) -> None:
        """
        Sends an error message when a WaniKani user wasn't registered yet with Crabigator.
        :param channel: The Discord.TextChannel that the message should be sent to.
        :param prefix: The prefix used for the Crabigator.
        """
        await channel.send(
            content=f'Crabigator does not know this person. '
            f'Please use `{prefix}adduser <WANIKANI_API_V2_TOKEN>` and try again.')

    @staticmethod
    async def oopsie(channel: discord.TextChannel, attempted_command: str, prefix: str) -> None:
        """
        Sends a generic error message if something went wrong.
        :param channel: The Discord.TextChannel that the message should be sent to.
        :param attempted_command: The Crabigator command that was attempted.
        :param prefix: The prefix used for the Crabigator.
        """
        await channel.send(
            content=f'Crabigator got too caught up studying and failed to handle `{prefix}{attempted_command}`. '
            f'Please notify my Overlord <@!209076181365030913>.')

    @staticmethod
    def split_text_into_lines(text: str, max_width: int, font: ImageFont) -> List[str]:
        # Shoutout to StackOverflow for this one.
        # https://stackoverflow.com/questions/43828154/breaking-a-string-along-whitespace-once-certain-width-is-exceeded-python
        lines: List[str] = []
        string: str = ''
        line_width: int = 0
        for c in text:
            line_width += font.getsize(c)[0]
            string += str(c)
            if line_width > max_width:
                line_width += font.getsize(c)[0]
                if line_width > max_width:
                    s = string.rsplit(" ", 1)
                    string = s[0]
                    lines.append(string)

                    try:
                        string = s[1]
                        line_width = len(string) * 5
                    except IndexError:
                        string = ""
                        line_width = 0
        # Leftover characters string should also be appended.
        if string:
            lines.append(string)

        return lines

    async def draw_on_sign(self, message: discord.Message, command: str, channel: discord.TextChannel, prefix: str):
        text: str = message.content.replace(f'{command} ', '', 1)
        if message.content.strip() == command:
            text = f'{prefix}draw <MESSAGE>'

        bg_image: Image = Image.open('img/crabigator_sign.png')
        text_image: Image = Image.open('img/to_draw_image.png')
        draw: ImageDraw = ImageDraw.Draw(text_image)
        font: ImageFont = ImageFont.truetype('/root/.fonts/TruetypewriterPolyglott-mELa.ttf', 40)
        # Change to this font for Windows machines.
        # font: ImageFont = ImageFont.truetype('arial.ttf', 40)
        # Split the text into lines based on width.
        lines = self.split_text_into_lines(text=text, max_width=200, font=font)
        # Only 3 lines of text fit on the sign.
        if len(lines) > 3:
            lines = self.split_text_into_lines(text='Max length exceeded!', max_width=200, font=font)
        y_spacing: int = 45
        y_val: int = 0
        # Determine where to start drawing based on the amount of lines.
        if len(lines) == 1:
            y_val = 70
        elif len(lines) == 2:
            y_val = 40
        elif len(lines) == 3:
            y_val = 10
        # Draw each line on the sign.
        for line in lines:
            line_x, line_y = font.getsize(text=line)
            draw.text(xy=(text_image.width - 235 - line_x / 2, y_val), text=line, font=font)
            y_val += y_spacing

        # Rotate text image before pasting it.
        text_image = text_image.convert('RGBA')
        text_image = text_image.rotate(angle=-12, resample=Image.NEAREST, expand=1, fillcolor='white')
        # Replace all the white with transparent.
        new_data = []
        for item in text_image.getdata():
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        text_image.putdata(data=new_data)

        bg_image.paste(text_image, (0, 0), text_image)

        bg_image.save(fp=f'img/drawnimage.png')
        await self.send_image(channel=channel, image_name=f'img/drawnimage.png')

    async def handle_command(self, message: discord.Message, prefix: str) -> None:
        """
        Handle requests (commands) given to the Crabigator.
        :param message: The Discord.Message that was received minus the prefix.
        :param prefix: The prefix used for the Crabigator.
        """
        words: List[str] = message.content.split(' ')
        command: str = words[0].lower()

        # Changes the prefix for the almighty Crabigator.
        if command in ['prefix']:
            # Only available in servers.
            if not message.guild:
                await message.channel.send(content="_Crabigator doesn't seem to listen to DM prefix requests..._")
                return

            if len(words) == 1:
                await message.channel.send(
                    content=f"Don't treat the prefix like your Kanji and forget it! "
                    f'Example usage: `{prefix}prefix <CHAR>`')
            elif len(words) > 2:
                await message.channel.send(
                    content=f'The Crabigator does not allow spaces in the prefix!')
            else:
                # Only server administrators should be allowed to touch the prefix.
                is_admin = False
                for r in message.author.roles:
                    # Bitwise AND operator can check that, for more information see the Discord API documentation at
                    # https://discordapp.com/developers/docs/topics/permissions
                    if (r.permissions.value & 0x00000008) == 0x00000008:
                        is_admin = True

                if is_admin:
                    self._dataStorage.insert_guild_prefix(guild_id=message.guild.id, prefix=words[1])
                    await message.channel.send(
                        content=f'The Crabigator became more omnipotent by changing to `{words[1]}`!')
                else:
                    await message.channel.send(
                        content=f'Only server administrators are allowed to change the prefix.')
        # Registers a WaniKani User for API calls.
        elif command in ['adduser', 'addme']:
            if message.guild:
                await message.channel.send(content="Let's do this in private, shall we? _(DM Crabigator instead)_")
            else:
                if len(words) == 1:
                    await message.channel.send(
                        content=f'Improper command usage. '
                        f'Example usage: `{prefix}adduser <WANIKANI_API_V2_TOKEN>`')
                elif len(words[1]) != 36 or '-' not in words[1]:
                    await message.channel.send(
                        content='API token is invalid! '
                                'Make sure there are no dangling characters on either side!')
                else:
                    if self._dataStorage.find_api_user(user_id=message.author.id):
                        await message.channel.send(
                            content='Your API key is already registered, did you mean `removeuser`?')
                        return
                    self._dataStorage.register_api_user(user_id=message.author.id, api_key=words[1])
                    # Initialize the key for future use.
                    self._dataFetcher.wanikani_users[message.author.id] = {}
                    await message.channel.send(
                        content=f'Crabigator has started watching <@{message.author.id}> closely...')
        # Deregisters a WaniKani User for API calls.
        elif command in ['removeuser', 'removeme']:
            if self._dataStorage.remove_api_user(user_id=message.author.id):
                emoji: discord.Emoji = await self.fetch_emoji(guild=message.guild,
                                                              emoji_array=['baka', 'pout', 'sad', 'cry'])
                await message.channel.send(
                    content=f"The Cult of the Crabigator didn't want you in the first place. {emoji}")
            else:
                emoji: discord.Emoji = await self.fetch_emoji(guild=message.guild,
                                                              emoji_array=['thinking', 'think', 'confused', 'shrug'])
                await message.channel.send(
                    content=f'Crabigator does not know this person. I cannot delete what I do not know. {emoji}')
        # Fetch a WaniKani User's overall stats.
        elif command in ['user', 'userstats']:
            await self.get_user_stats(words=words, message=message, author=message.author, prefix=prefix)
        # Fetch a WaniKani User's daily stats.
        elif command in ['daily', 'dailyoverview', 'dailystatus', 'dailystats']:
            await self.get_daily_stats(words=words, channel=message.channel, author=message.author, prefix=prefix)
        # Fetch a WaniKani User's leveling statistics.
        elif command in ['levelstats', 'levelstats', 'leveling', 'levelingstatus', 'levelingstats']:
            await self.get_leveling_stats(words=words, channel=message.channel, author=message.author, prefix=prefix)
        elif command in ['draw', 'certify']:
            await self.draw_on_sign(command=command, message=message, channel=message.channel, prefix=prefix)
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
        elif command in ['help', 'h', 'commands']:
            await self.get_help(words=words, channel=message.channel, prefix=prefix)
        # Unknown Command.
        else:
            await message.channel.send(
                content=f'Crabigator has yet to learn this ~~kanji~~ command. '
                f'Refer to `{prefix}help` to see what I can do!')

    async def get_user_data_model(self, user_id: int) -> User:
        """
        Get the user_data field from the DataFetcher as a User object.
        :param user_id: The Discord.User.id that was used to as the dictionary key.
        """
        if user_id not in self._dataFetcher.wanikani_users.keys():
            self._dataFetcher.wanikani_users[user_id] = {}
        if 'USER_DATA' not in self._dataFetcher.wanikani_users[user_id]:
            await self._dataFetcher.fetch_wanikani_user_data(user_id=user_id)
        return self._dataFetcher.wanikani_users[user_id]['USER_DATA']

    @staticmethod
    def extract_user_id(words: List[str], author: discord.member.Member) -> int:
        """
        Extracts the Discord.User.id from the author or message if applicable. Returns -1 if no match.
        :param words: The string message that was sent.
        :param author: The Discord.User author of the message.
        :return: The ID of the author or of the tagged user. -1 if the message is too long (>2 words).
        """
        if len(words) == 1:
            return author.id
        elif len(words) == 2:
            # User got tagged with <@!NUMBER>
            if words[1].startswith('<@!') and words[1].endswith('>'):
                return int(words[1].lstrip('<@!').rstrip('>'))
            else:
                try:
                    return int(words[1])
                except TypeError:
                    return -1
        return -1

    async def get_user_stats(self, words: List[str], message: discord.Message,
                             author: discord.member.Member, prefix: str) -> None:
        """
        Fetches and displays a WaniKani user.
        :param words: Array of arguments, if there is a second one it is a specific Discord.User.
        :param message: The Discord.Message that was received minus the prefix.
        :param author: The Discord.User that requested the statistics.
        :param prefix: The prefix used for the Crabigator.
        """
        user_id = self.extract_user_id(words=words, author=author)
        if user_id == -1:
            await message.channel.send(content='Please tag **one** Discord User,'
                                       ' or provide **one** Discord User ID with this command.')
            return

        if not self._dataStorage.find_api_user(user_id=user_id):
            await self.unknown_wanikani_user(channel=message.channel, prefix=prefix)
            return

        if user_id not in self._dataFetcher.wanikani_users.keys():
            self._dataFetcher.wanikani_users[user_id] = {}

        user: User = await self._dataFetcher.fetch_wanikani_user_data(user_id=user_id)
        embed: discord.Embed = discord.Embed(title=user.username, url=user.profile_url,
                                             colour=author.colour, timestamp=datetime.now())
        embed.set_thumbnail(url='https://cdn.wanikani.com/default-avatar-300x300-20121121.png')
        summary: Summary = await self._dataFetcher.fetch_wanikani_user_summary(user_id=user_id)
        # Add all the custom embed fields.
        embed.add_field(name='Level', value=f'{user.level}/{user.max_level}', inline=False)
        # Get a good and bad emoji from the Guild.
        happy_emoji: discord.Emoji = await self.fetch_emoji(message.guild, ['happy', 'yay', 'thumbsup', 'sugoi'])
        if not happy_emoji:
            happy_emoji = ':thumbsup:'
        sad_emoji: discord.Emoji = await self.fetch_emoji(message.guild, ['sad', 'cry', 'thumbsdown', 'baka'])
        if not sad_emoji:
            sad_emoji = ':thumbsdown:'
        if user.subscribed:
            embed.add_field(name='Subscription Status',
                            value=f"**{user.subscription_type.capitalize()}** cultist member since"
                            f" {user.member_since[0:user.member_since.index('T')]} {happy_emoji}",
                            inline=False)
        else:
            embed.add_field(name='Subscription Status', value=f"Wannabe cultist... {sad_emoji}", inline=False)
        # Fetch counts of radicals, kanji and vocabulary learned and burned.
        item_counts: List[int] = await self._dataFetcher.fetch_wanikani_item_counts(user_id=user_id)
        embed.add_field(name='Radicals Learned:', value=str(item_counts[0]), inline=True)
        embed.add_field(name='Kanji Learned:', value=str(item_counts[1]), inline=True)
        embed.add_field(name='Vocabulary Learned:', value=str(item_counts[2]), inline=True)
        embed.add_field(name='Items Burned:', value=str(item_counts[3]), inline=False)
        embed.add_field(name='Lessons available:', value=str(len(summary.available_lessons)), inline=True)
        embed.add_field(name='Reviews available:', value=str(len(summary.available_reviews)), inline=True)
        await self.send_embed(channel=message.channel, embed=embed)

    async def get_daily_stats(self, words: List[str], channel: discord.TextChannel,
                              author: discord.member.Member, prefix: str) -> None:
        """
        Fetches the user's daily statistics and returns them neatly formatted.
        :param words: Array of arguments, if there is a second one it is a specific Discord.User.
        :param channel: The Discord.TextChannel that the message should be sent to.
        :param author: The Discord.User that requested the statistics.
        :param prefix: The prefix used for the Crabigator.
        """
        user_id = self.extract_user_id(words=words, author=author)
        if user_id == -1:
            await channel.send(content='Please tag **one** Discord User,'
                                       ' or provide **one** Discord User ID with this command.')
            return

        if not self._dataStorage.find_api_user(user_id=user_id):
            await self.unknown_wanikani_user(channel=channel, prefix=prefix)
            return

        if user_id not in self._dataFetcher.wanikani_users.keys():
            self._dataFetcher.wanikani_users[user_id] = {}

        user: User = await self.get_user_data_model(user_id=user_id)
        date: str = datetime.today().strftime('%Y-%m-%d')
        lesson_data: Dict[str, Any] = await self._dataFetcher.get_wanikani_data(user_id=user_id,
                                                                                resource='assignments',
                                                                                after_date=date)
        review_data: Dict[str, Any] = await self._dataFetcher.get_wanikani_data(user_id=user_id,
                                                                                resource='reviews',
                                                                                after_date=date)
        summary_data: Summary = await self._dataFetcher.fetch_wanikani_user_summary(user_id=user_id)
        embed: discord.Embed = discord.Embed(title='Daily Overview',
                                             colour=author.colour,
                                             timestamp=datetime.now())
        embed.set_thumbnail(url='https://cdn.wanikani.com/default-avatar-300x300-20121121.png')
        embed.set_author(name='WaniKani Profile', icon_url='https://knowledge.wanikani.com/siteicon.png',
                         url=user.profile_url)
        # Add all the custom embed fields.
        embed.add_field(name='Completed Reviews',
                        value=review_data['total_count'],
                        inline=False)
        """
        The total count for lessons in the /assignments resource is incorrect.
        Instead of only showing the newest lessons since the ?updated_after query,
        it shows 'lessons' that already have high srs_stages.
        So to get the actual amount we need to loop through and parse the ones started after the current date.
        So for example started_at being 2019-05-24 for the completed lessons on may 24th 2019.
        """
        completed_lessons: int = 0
        for entry in lesson_data['data']:
            # Parse the started_at date from the entry.
            if entry['data']['started_at'] \
                    and date == entry['data']['started_at'][0:entry['data']['started_at'].index('T')]:
                completed_lessons += 1
        embed.add_field(name='Completed Lessons',
                        value=str(completed_lessons),
                        inline=False)
        embed.add_field(name='Reviews available:',
                        value=str(len(summary_data.available_reviews)),
                        inline=False)
        embed.add_field(name='Lessons available:',
                        value=str(len(summary_data.available_lessons)),
                        inline=False)
        await self.send_embed(channel=channel, embed=embed)

    async def get_leveling_stats(self, words: List[str], channel: discord.TextChannel,
                                 author: discord.member.Member, prefix: str):
        """
        Fetches the leveling statistics and returns them neatly formatted.
        :param words: Array of arguments, if there is a second one it is a specific Discord.User.
        :param channel: The Discord.TextChannel that the message should be sent to.
        :param author: The Discord.User that requested the statistics.
        :param prefix: The prefix used for the Crabigator.
        """
        user_id = self.extract_user_id(words=words, author=author)
        if user_id == -1:
            await channel.send(content='Please tag **one** Discord User,'
                                       ' or provide **one** Discord User ID with this command.')
            return

        if not self._dataStorage.find_api_user(user_id=user_id):
            await self.unknown_wanikani_user(channel=channel, prefix=prefix)
            return

        user: User = await self.get_user_data_model(user_id=user_id)
        progression: Dict[str, Any] = await self._dataFetcher.get_wanikani_data(user_id=user_id,
                                                                                resource='level_progressions')
        # Add found data to user object.
        for level_progress in progression['data']:
            user.level_progressions.append(level_progress)
        await channel.send(
            content=f"Compiling your data took forever, so I took a nap instead. "
            f"Just use https://www.wkstats.com/ for now or bitch at <@!209076181365030913>.")

    async def get_help(self, words: List[str], channel: discord.TextChannel, prefix: str):
        """
        Shows the help menu with all the known commands or the specified command in the arguments.
        :param words: Array of arguments, either just 'help' but can also include a command name afterwards.
        :param channel: The Discord.TextChannel that the message should be sent to.
        :param prefix: The prefix used for the Crabigator.
        """
        if len(words) == 1:
            embed: discord.Embed = discord.Embed(title=f"{self.user.display_name} Commands Help",
                                                 colour=self.user.colour,
                                                 timestamp=datetime(year=2019, month=11, day=24))
            embed.set_thumbnail(url='https://i.imgur.com/Fjk2Dv1.png')
            embed.set_author(name=self.user.display_name, icon_url=self.user.avatar_url,
                             url='https://github.com/AlexanderColen/WaniKaniDiscordBot')
            # Add all the custom embed fields.
            embed.add_field(name=f'{prefix}help',
                            value='Displays this embedded message.',
                            inline=False)
            embed.add_field(name=f'{prefix}help `<COMMAND_NAME>`',
                            value='Displays more info for the specified command.',
                            inline=False)
            embed.add_field(name=f'{prefix}adduser `<WANIKANI_API_V2_TOKEN>`',
                            value='Registers a WaniKani user to allow API usage. **ONLY WORKS IN DIRECT MESSAGES!**',
                            inline=False)
            embed.add_field(name=f'{prefix}removeuser',
                            value="Removes a user's data to no longer allow API usage.",
                            inline=False)
            embed.add_field(name=f'{prefix}user',
                            value="Displays the WaniKani user's overall statistics."
                                  "Optionally you can target another user.",
                            inline=False)
            embed.add_field(name=f'{prefix}levelstats',
                            value="Displays the WaniKani user's leveling statistics. "
                                  "Optionally you can target another user.",
                            inline=False)
            embed.add_field(name=f'{prefix}draw',
                            value="Draws your message on a sign.",
                            inline=False)
            embed.add_field(name=f'{prefix}congratulations',
                            value=':tada:',
                            inline=True)
            embed.add_field(name=f'{prefix}anger',
                            value=':anger:',
                            inline=True)
            embed.add_field(name=f'{prefix}love',
                            value=':heart:',
                            inline=True)
            await self.send_embed(channel=channel, embed=embed)
        else:
            if words[1] == 'help':
                await self.send_image(channel=channel, image_name='img/yodawg.png')
            else:
                title: str = f"{self.user.display_name}'s `{prefix}{words[1]}` Command Assistance"
                embed: discord.Embed = discord.Embed(title=title,
                                                     colour=self.user.colour,
                                                     timestamp=datetime(year=2019, month=11, day=24))
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

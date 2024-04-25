import inspect, sys, time, discord, requests, os

from bot import ModerationBot
from commands.base import Command
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
try:
    TOKEN = open(os.path.join(__location__, "token.txt"), "r").read().strip("\n")
except FileNotFoundError:
    quit("Please create a token.txt file and place your token in it!")
if TOKEN is None:
    quit("Please create a token.txt file and place your token in it!")

class SpyPetBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "spypet_ban"
        self.client = client_instance
        self.usage = "Usage: {self.client.prefix}spypet_ban"
    
    async def execute(self, ctx: discord.Message, **kwargs) -> None:
        GUILD_ID = ctx.guild.id
        REASON = 'spy.pet bot'

        selfbots = requests.get('https://gist.githubusercontent.com/Dziurwa14/05db50c66e4dcc67d129838e1b9d739a/raw/b0c0ebba557521e9234074a22e544ab48f448f6a/spy.pet%20accounts').json()

        headers = {
            'Authorization': f'Bot {TOKEN}',
            'X-Audit-Log-Reason': REASON
        }

        data = {
            'user_ids': selfbots
        }

        response = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/bulk-ban", headers=headers, json=data)

        if response.status_code == 200:
            await ctx.author.send("Banned selfbots successfully.")
        else:
            await ctx.author.send(f"Failed to ban selfbots. Status code: {response.status_code}")


class HardBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "hard_ban"
        self.client = client_instance
        self.usage = f"Usage: {self.client.prefix}hard_ban <user ID> <reason>"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.client.storage):
            if len(command) >= 2:
                if is_integer(command[0]):
                    user_id = int(command[0])
                    guild_id = str(message.guild.id)
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    
                    if user is not None:
                        temp = [item for item in command if command.index(item) > 0]
                        reason = " ".join(temp)
                        await message.guild.ban(user, reason=reason)
                        
                        embed_builder = EmbedBuilder(event="hard_ban")
                        await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                        await embed_builder.add_field(name="**Hard Banned user**", value=f"`{user.name}`")
                        await embed_builder.add_field(name="**Reason**", value=f"`{reason}`")
                        embed = await embed_builder.get_embed()
                        
                        log_channel_id = int(self.client.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                        
                        await message.channel.send(f"**Hard banned user:** `{user.name}` **Reason:** `{reason}`")
                    else:
                        await message.channel.send(f"There is no user with the userID: {user_id}.")
                else:
                    await message.channel.send(f"{command[0]} is not a valid user ID.")
            else:
                await message.channel.send("You must provide a user ID and a reason.")
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class UnBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "unban"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}unban <user ID>"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to unban. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) == 1:
                if is_integer(command[0]):
                    user_id = int(command[0])
                    guild_id = str(message.guild.id)
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    if user is not None:
                        # Unban the user and remove them from the guilds banned users list
                        await message.guild.unban(user, reason=f"Unbanned by {message.author.name}")
                        self.storage.settings["guilds"][guild_id]["banned_users"].pop(str(user_id))
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(f"**Unbanned user:** `{user.name}`**.**")
                        
                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="unban")
                        await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                        await embed_builder.add_field(name="**Unbanned user**", value=f"`{user.name}`")
                        embed = await embed_builder.get_embed()
                        log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")
    

class TempBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "ban"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}soft_ban <user ID> <duration> <reason>"
        self.invalid_user = "There is no user with the user ID: {user_id}. {usage}"
        self.invalid_duration = "The duration provided is invalid. The duration must be a string that looks like: 1w3d5h30m20s or a positive number in seconds. {usage}"
        self.not_enough_arguments = "You must provide a user to ban. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 3:
                if is_integer(command[0]):
                    user_id = int(command[0])
                    duration = parse_duration(command[1])
                    if is_valid_duration(duration):
                        guild_id = str(message.guild.id)
                        ban_duration = int(time.time()) + duration
                        try:
                            user = await message.guild.fetch_member(user_id)
                        except discord.errors.NotFound or discord.errors.HTTPException:
                            user = None
                        # Collects everything after the first two items in the command and uses it as a reason.
                        temp = [item for item in command if command.index(item) > 1]
                        reason = " ".join(temp)
                        if user is not None:
                            # Add the muted role and store them in guilds muted users list. We use -1 as the duration to state that it lasts forever.
                            await message.guild.ban(user, reason=reason)
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)] = {}
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)]["duration"] = ban_duration
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)]["reason"] = reason
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)]["normal_duration"] = command[1]
                            await self.storage.write_file_to_disk()
                            # Message the channel
                            await message.channel.send(f"**Temporarily banned user:** `{user.name}` **for:** `{command[1]}`**. Reason:** `{reason}`")
                            
                            # Build the embed and message it to the log channel
                            embed_builder = EmbedBuilder(event="tempban")
                            await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                            await embed_builder.add_field(name="**Temp Banned user**", value=f"`{user.name}`")
                            await embed_builder.add_field(name="**Reason**", value=f"`{reason}`")
                            await embed_builder.add_field(name="**Duration**", value=f"`{command[1]}`")
                            embed = await embed_builder.get_embed()
                            log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel is not None:
                                await log_channel.send(embed=embed)
                        else:
                            await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)

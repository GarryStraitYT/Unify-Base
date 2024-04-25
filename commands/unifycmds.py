import inspect, sys, time, discord, requests, os, subprocess, re

from bot import ModerationBot
from commands.base import Command
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)


class neofetchCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "neofetch"
        self.client = client_instance
        self.usage = "Usage: {self.client.prefix}neofetch"
    async def execute(self, message: discord.Message, **kwargs) -> None:
        # Run neofetch command
        try:
            result = subprocess. run(['neofetch', '--off', '--stdout'], capture_output=True, text=True)
            output = result.stdout
            # await message.channel.send()
            # Strip color coding using regex
            output_formatted = output.replace('\n', '\n\n')
            output_stripped = re.sub(r'\x1b\[[0-9;]*m', '', output_formatted)

            # Send the result as a message
            await message.channel.send(output)
        
        except Exception as e:
            await message.channel.send(f'Error: {e}')

classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)

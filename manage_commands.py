"""
Command management utility for Discord Music Bot.

This script provides utilities for managing Discord slash commands,
including syncing, clearing, and testing command registration.
"""

import asyncio
import argparse
import logging
import sys
from typing import Optional

import discord
from discord.ext import commands

from config import BOT_TOKEN, BOT_PREFIX
from register_commands import CommandRegistrar


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommandManager:
    """Manages Discord command registration and synchronization."""
    
    def __init__(self, token: str):
        self.token = token
        self.bot: Optional[commands.Bot] = None
        self.registrar: Optional[CommandRegistrar] = None
    
    async def setup_bot(self) -> None:
        """Set up the bot instance."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        self.bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)
        self.registrar = CommandRegistrar(self.bot)
        
        @self.bot.event
        async def on_ready():
            logger.info(f"Bot connected as {self.bot.user}")
    
    async def sync_global(self) -> None:
        """Sync commands globally."""
        if not self.bot:
            await self.setup_bot()
        
        await self.bot.login(self.token)
        
        try:
            logger.info("Syncing commands globally...")
            synced = await self.registrar.sync_commands()
            logger.info(f"Successfully synced {len(synced)} commands globally")
            logger.warning("Note: Global sync can take up to 1 hour to propagate")
            
        except Exception as e:
            logger.error(f"Error syncing commands globally: {e}")
        finally:
            await self.bot.close()
    
    async def sync_guild(self, guild_id: int) -> None:
        """Sync commands to a specific guild."""
        if not self.bot:
            await self.setup_bot()
        
        await self.bot.login(self.token)
        
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                # Try to fetch the guild
                guild = await self.bot.fetch_guild(guild_id)
            
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return
            
            logger.info(f"Syncing commands to guild: {guild.name} ({guild_id})")
            synced = await self.registrar.sync_commands(guild)
            logger.info(f"Successfully synced {len(synced)} commands to {guild.name}")
            
        except Exception as e:
            logger.error(f"Error syncing commands to guild {guild_id}: {e}")
        finally:
            await self.bot.close()
    
    async def clear_global(self) -> None:
        """Clear all global commands."""
        if not self.bot:
            await self.setup_bot()
        
        await self.bot.login(self.token)
        
        try:
            logger.info("Clearing all global commands...")
            await self.registrar.clear_commands()
            logger.info("Successfully cleared all global commands")
            
        except Exception as e:
            logger.error(f"Error clearing global commands: {e}")
        finally:
            await self.bot.close()
    
    async def clear_guild(self, guild_id: int) -> None:
        """Clear commands from a specific guild."""
        if not self.bot:
            await self.setup_bot()
        
        await self.bot.login(self.token)
        
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                guild = await self.bot.fetch_guild(guild_id)
            
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return
            
            logger.info(f"Clearing commands from guild: {guild.name} ({guild_id})")
            await self.registrar.clear_commands(guild)
            logger.info(f"Successfully cleared commands from {guild.name}")
            
        except Exception as e:
            logger.error(f"Error clearing commands from guild {guild_id}: {e}")
        finally:
            await self.bot.close()
    
    async def list_commands(self, guild_id: Optional[int] = None) -> None:
        """List registered commands."""
        if not self.bot:
            await self.setup_bot()
        
        await self.bot.login(self.token)
        
        try:
            if guild_id:
                guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
                if not guild:
                    logger.error(f"Guild {guild_id} not found")
                    return
                commands = self.bot.tree.get_commands(guild=guild)
                logger.info(f"Commands in guild {guild.name} ({guild_id}):")
            else:
                commands = self.bot.tree.get_commands()
                logger.info("Global commands:")
            
            if not commands:
                logger.info("No commands found")
            else:
                for cmd in commands:
                    logger.info(f"  - /{cmd.name}: {cmd.description}")
            
        except Exception as e:
            logger.error(f"Error listing commands: {e}")
        finally:
            await self.bot.close()


async def main() -> None:
    """Main function for command management CLI."""
    parser = argparse.ArgumentParser(description="Discord Music Bot Command Manager")
    
    subparsers = parser.add_subparsers(dest='action', help='Available actions')
    
    # Sync commands
    sync_parser = subparsers.add_parser('sync', help='Sync commands')
    sync_parser.add_argument('--guild', type=int, help='Guild ID to sync to (for testing)')
    
    # Clear commands
    clear_parser = subparsers.add_parser('clear', help='Clear commands')
    clear_parser.add_argument('--guild', type=int, help='Guild ID to clear from')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List registered commands')
    list_parser.add_argument('--guild', type=int, help='Guild ID to list commands from')
    
    args = parser.parse_args()
    
    if not BOT_TOKEN:
        logger.error("❌ Bot token not found!")
        logger.error("Please set DISCORD_BOT_TOKEN environment variable or create .env file")
        sys.exit(1)
    
    manager = CommandManager(BOT_TOKEN)
    
    try:
        if args.action == 'sync':
            if args.guild:
                await manager.sync_guild(args.guild)
            else:
                await manager.sync_global()
        
        elif args.action == 'clear':
            if args.guild:
                await manager.clear_guild(args.guild)
            else:
                await manager.clear_global()
        
        elif args.action == 'list':
            await manager.list_commands(args.guild)
        
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Handle Windows event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())

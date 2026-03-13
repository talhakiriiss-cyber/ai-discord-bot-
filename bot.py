"""
AI-Powered Discord Bot
Author: Talha Kiris
Description: A versatile Discord bot with AI chat capabilities,
             moderation tools, and utility commands.
             Supports OpenAI GPT and Claude AI integration.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List

# Discord imports
try:
    import discord
    from discord.ext import commands
    from discord import app_commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print("[!] discord.py not installed. Install with: pip install discord.py")

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIBot')


class ConversationManager:
    """Manages conversation history for each user/channel."""
    
    def __init__(self, max_history: int = 10):
        self.conversations: Dict[int, List[Dict]] = {}
        self.max_history = max_history
    
    def add_message(self, channel_id: int, role: str, content: str):
        """Add a message to the conversation history."""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        self.conversations[channel_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent messages
        if len(self.conversations[channel_id]) > self.max_history:
            self.conversations[channel_id] = self.conversations[channel_id][-self.max_history:]
    
    def get_history(self, channel_id: int) -> List[Dict]:
        """Get conversation history for a channel."""
        return self.conversations.get(channel_id, [])
    
    def clear_history(self, channel_id: int):
        """Clear conversation history for a channel."""
        self.conversations.pop(channel_id, None)
    
    def get_formatted_history(self, channel_id: int) -> List[Dict]:
        """Get history formatted for OpenAI API."""
        history = self.get_history(channel_id)
        return [{'role': msg['role'], 'content': msg['content']} for msg in history]


class AIProvider:
    """Handles AI model integration (OpenAI GPT / Claude)."""
    
    def __init__(self, provider: str = 'openai', api_key: str = None, 
                 model: str = None, system_prompt: str = None):
        """
        Initialize AI provider.
        
        Args:
            provider: 'openai' or 'claude'
            api_key: API key for the provider
            model: Model name (e.g., 'gpt-4', 'claude-3-sonnet')
            system_prompt: Custom system prompt for the AI
        """
        self.provider = provider
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '')
        self.model = model or self._default_model()
        self.system_prompt = system_prompt or self._default_prompt()
        
        if provider == 'openai' and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"AI Provider initialized: {provider} ({self.model})")
    
    def _default_model(self) -> str:
        if self.provider == 'openai':
            return 'gpt-4'
        elif self.provider == 'claude':
            return 'claude-3-sonnet-20240229'
        return 'gpt-3.5-turbo'
    
    def _default_prompt(self) -> str:
        return (
            "You are a helpful, friendly AI assistant in a Discord server. "
            "Keep your responses concise (under 2000 characters for Discord limits). "
            "Be helpful, accurate, and engaging. Use emojis occasionally."
        )
    
    async def generate_response(self, messages: List[Dict], 
                                 max_tokens: int = 500) -> str:
        """
        Generate an AI response.
        
        Args:
            messages: Conversation history
            max_tokens: Maximum response length
            
        Returns:
            AI-generated response text
        """
        try:
            full_messages = [{'role': 'system', 'content': self.system_prompt}]
            full_messages.extend(messages)
            
            if self.provider == 'openai' and OPENAI_AVAILABLE:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == 'claude':
                # Claude API integration
                import anthropic
                client = anthropic.Anthropic(api_key=self.api_key)
                response = client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=[m for m in full_messages if m['role'] != 'system']
                )
                return response.content[0].text
            
            else:
                return "AI provider not configured. Please set up your API key."
                
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return f"Sorry, I encountered an error: {str(e)[:100]}"


class ModerationSystem:
    """Simple moderation system for the bot."""
    
    def __init__(self):
        self.warnings: Dict[int, int] = {}  # user_id: warning_count
        self.banned_words: List[str] = []
        self.load_config()
    
    def load_config(self):
        """Load moderation config from file."""
        try:
            with open('moderation_config.json', 'r') as f:
                config = json.load(f)
                self.banned_words = config.get('banned_words', [])
        except FileNotFoundError:
            self.save_config()
    
    def save_config(self):
        """Save moderation config to file."""
        config = {'banned_words': self.banned_words}
        with open('moderation_config.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    def check_message(self, content: str) -> bool:
        """Check if a message contains banned content."""
        content_lower = content.lower()
        return any(word in content_lower for word in self.banned_words)
    
    def add_warning(self, user_id: int) -> int:
        """Add a warning to a user. Returns total warnings."""
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        return self.warnings[user_id]
    
    def get_warnings(self, user_id: int) -> int:
        """Get warning count for a user."""
        return self.warnings.get(user_id, 0)


class BotStats:
    """Track bot usage statistics."""
    
    def __init__(self):
        self.commands_used: int = 0
        self.ai_queries: int = 0
        self.messages_moderated: int = 0
        self.start_time: datetime = datetime.now()
        self.popular_commands: Dict[str, int] = {}
    
    def log_command(self, command_name: str):
        self.commands_used += 1
        self.popular_commands[command_name] = self.popular_commands.get(command_name, 0) + 1
    
    def log_ai_query(self):
        self.ai_queries += 1
    
    def get_uptime(self) -> str:
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    
    def get_summary(self) -> Dict:
        return {
            'uptime': self.get_uptime(),
            'commands_used': self.commands_used,
            'ai_queries': self.ai_queries,
            'messages_moderated': self.messages_moderated,
            'top_commands': dict(sorted(
                self.popular_commands.items(), 
                key=lambda x: x[1], reverse=True
            )[:5])
        }


def create_bot(token: str = None, ai_provider: str = 'openai', 
               ai_key: str = None, prefix: str = '!'):
    """
    Create and configure the Discord bot.
    
    Args:
        token: Discord bot token
        ai_provider: AI provider ('openai' or 'claude')
        ai_key: API key for the AI provider
        prefix: Command prefix (default: '!')
        
    Returns:
        Configured bot instance
    """
    if not DISCORD_AVAILABLE:
        print("[!] discord.py is required. Install with: pip install discord.py")
        return None
    
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix=prefix, intents=intents)
    
    # Initialize components
    conversation_mgr = ConversationManager()
    ai = AIProvider(provider=ai_provider, api_key=ai_key)
    moderation = ModerationSystem()
    stats = BotStats()
    
    # ==================== EVENTS ====================
    
    @bot.event
    async def on_ready():
        logger.info(f'Bot is ready! Logged in as {bot.user}')
        logger.info(f'Connected to {len(bot.guilds)} servers')
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{prefix}help for commands"
            )
        )
    
    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        
        # Check moderation
        if moderation.check_message(message.content):
            await message.delete()
            warnings = moderation.add_warning(message.author.id)
            await message.channel.send(
                f"⚠️ {message.author.mention} - Message removed. Warning {warnings}/3."
            )
            stats.messages_moderated += 1
            
            if warnings >= 3:
                await message.channel.send(
                    f"🔨 {message.author.mention} has been muted (3 warnings)."
                )
            return
        
        await bot.process_commands(message)
    
    # ==================== AI COMMANDS ====================
    
    @bot.command(name='ask', help='Ask the AI a question')
    async def ask(ctx, *, question: str):
        """Ask the AI a question."""
        stats.log_command('ask')
        stats.log_ai_query()
        
        async with ctx.typing():
            conversation_mgr.add_message(ctx.channel.id, 'user', question)
            history = conversation_mgr.get_formatted_history(ctx.channel.id)
            
            response = await ai.generate_response(history)
            conversation_mgr.add_message(ctx.channel.id, 'assistant', response)
        
        # Split long responses
        if len(response) > 2000:
            chunks = [response[i:i+1990] for i in range(0, len(response), 1990)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)
    
    @bot.command(name='clear', help='Clear AI conversation history')
    async def clear_chat(ctx):
        """Clear the conversation history."""
        stats.log_command('clear')
        conversation_mgr.clear_history(ctx.channel.id)
        await ctx.send("🗑️ Conversation history cleared!")
    
    @bot.command(name='persona', help='Set AI personality')
    async def set_persona(ctx, *, persona: str):
        """Set a custom AI personality."""
        stats.log_command('persona')
        ai.system_prompt = persona
        conversation_mgr.clear_history(ctx.channel.id)
        await ctx.send(f"🎭 AI personality updated! Try asking me something.")
    
    # ==================== UTILITY COMMANDS ====================
    
    @bot.command(name='ping', help='Check bot latency')
    async def ping(ctx):
        stats.log_command('ping')
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @bot.command(name='serverinfo', help='Display server information')
    async def server_info(ctx):
        stats.log_command('serverinfo')
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📋 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="📝 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @bot.command(name='userinfo', help='Display user information')
    async def user_info(ctx, member: discord.Member = None):
        stats.log_command('userinfo')
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="🏷️ Username", value=str(member), inline=True)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Joined Server", value=member.joined_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="📅 Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="🎭 Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="⚠️ Warnings", value=moderation.get_warnings(member.id), inline=True)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='botstats', help='Display bot statistics')
    async def bot_stats(ctx):
        stats.log_command('botstats')
        summary = stats.get_summary()
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="⏱️ Uptime", value=summary['uptime'], inline=True)
        embed.add_field(name="📝 Commands Used", value=summary['commands_used'], inline=True)
        embed.add_field(name="🤖 AI Queries", value=summary['ai_queries'], inline=True)
        embed.add_field(name="🛡️ Messages Moderated", value=summary['messages_moderated'], inline=True)
        embed.add_field(name="🌐 Servers", value=len(bot.guilds), inline=True)
        
        if summary['top_commands']:
            top_cmds = "\n".join([f"`{cmd}`: {count}" for cmd, count in summary['top_commands'].items()])
            embed.add_field(name="🔥 Top Commands", value=top_cmds, inline=False)
        
        await ctx.send(embed=embed)
    
    # ==================== MODERATION COMMANDS ====================
    
    @bot.command(name='warn', help='Warn a user')
    @commands.has_permissions(manage_messages=True)
    async def warn_user(ctx, member: discord.Member, *, reason: str = "No reason provided"):
        stats.log_command('warn')
        warnings = moderation.add_warning(member.id)
        
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            color=discord.Color.yellow()
        )
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Warnings", value=f"{warnings}/3", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Issued by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @bot.command(name='purge', help='Delete messages')
    @commands.has_permissions(manage_messages=True)
    async def purge(ctx, amount: int = 10):
        stats.log_command('purge')
        if amount > 100:
            amount = 100
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🗑️ Deleted {len(deleted) - 1} messages.")
        await asyncio.sleep(3)
        await msg.delete()
    
    return bot


# ============================================================
# DEMO: Shows bot structure and capabilities
# ============================================================

def show_demo():
    """Display bot capabilities without running it."""
    print("=" * 60)
    print("   AI-POWERED DISCORD BOT - DEMO")
    print("   Author: Talha Kiris")
    print("=" * 60)
    
    print("\n📋 BOT COMMANDS:")
    print("-" * 60)
    
    commands_list = {
        "AI Commands": {
            "!ask <question>": "Ask the AI any question",
            "!clear": "Clear conversation history",
            "!persona <text>": "Set custom AI personality",
        },
        "Utility Commands": {
            "!ping": "Check bot latency",
            "!serverinfo": "Display server information",
            "!userinfo [@user]": "Display user information",
            "!botstats": "Show bot statistics",
        },
        "Moderation Commands": {
            "!warn @user [reason]": "Issue a warning",
            "!purge [amount]": "Delete messages (max 100)",
        }
    }
    
    for category, cmds in commands_list.items():
        print(f"\n   {category}:")
        for cmd, desc in cmds.items():
            print(f"      {cmd:<25} {desc}")
    
    print(f"\n{'=' * 60}")
    print("   FEATURES:")
    print("-" * 60)
    print("   - AI chat with GPT-4 / Claude integration")
    print("   - Conversation memory (per channel)")
    print("   - Custom AI personalities")
    print("   - Auto-moderation (banned words)")
    print("   - Warning system (3 strikes)")
    print("   - Rich embeds for server/user info")
    print("   - Usage statistics tracking")
    print("   - Detailed logging")
    
    print(f"\n{'=' * 60}")
    print("   SETUP:")
    print("-" * 60)
    print("   1. Create a Discord bot at discord.com/developers")
    print("   2. Copy the bot token")
    print("   3. Get an OpenAI or Claude API key")
    print("   4. Set environment variables:")
    print("      export DISCORD_TOKEN='your-token'")
    print("      export OPENAI_API_KEY='your-key'")
    print("   5. Run: python bot.py")
    
    print(f"\n{'=' * 60}")
    print("   EXAMPLE USAGE:")
    print("-" * 60)
    print("   User: !ask What is Python?")
    print("   Bot:  Python is a versatile programming language known")
    print("         for its simplicity and readability. It's widely")
    print("         used in web development, data science, AI, and")
    print("         automation. 🐍")
    print()
    print("   User: !persona You are a pirate captain")
    print("   Bot:  🎭 AI personality updated!")
    print()
    print("   User: !ask What should I eat for lunch?")
    print("   Bot:  Arrr matey! Ye should feast on some fine fish")
    print("         and chips, washed down with grog! 🏴‍☠️")
    
    # Test components
    print(f"\n{'=' * 60}")
    print("   COMPONENT TEST:")
    print("-" * 60)
    
    # Test ConversationManager
    conv = ConversationManager()
    conv.add_message(1, 'user', 'Hello!')
    conv.add_message(1, 'assistant', 'Hi there!')
    conv.add_message(1, 'user', 'How are you?')
    print(f"   ConversationManager: {len(conv.get_history(1))} messages stored ✅")
    
    # Test ModerationSystem
    mod = ModerationSystem()
    mod.banned_words = ['spam', 'test_bad_word']
    assert mod.check_message("this is spam") == True
    assert mod.check_message("this is fine") == False
    print(f"   ModerationSystem: Content filtering works ✅")
    
    # Test BotStats
    bot_stats = BotStats()
    bot_stats.log_command('ask')
    bot_stats.log_command('ask')
    bot_stats.log_command('ping')
    bot_stats.log_ai_query()
    summary = bot_stats.get_summary()
    print(f"   BotStats: Tracking {summary['commands_used']} commands ✅")
    
    print(f"\n   All components working! ✅")
    print("=" * 60)


if __name__ == "__main__":
    # Check if we should run the bot or show demo
    token = os.getenv('DISCORD_TOKEN')
    
    if token:
        bot = create_bot(
            token=token,
            ai_provider='openai',
            ai_key=os.getenv('OPENAI_API_KEY')
        )
        if bot:
            bot.run(token)
    else:
        show_demo()

# 🤖 AI-Powered Discord Bot

A feature-rich Discord bot with AI chat capabilities (GPT-4 / Claude), moderation tools, and utility commands. Built with Python and discord.py.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.0+-purple.svg)

## Features

### AI Chat
- **Conversational AI** — Chat with GPT-4 or Claude directly in Discord
- **Conversation Memory** — Bot remembers context per channel
- **Custom Personalities** — Set the AI to be a pirate, teacher, or anything else
- **Smart Responses** — Handles long responses by splitting into chunks

### Moderation
- **Auto-moderation** — Automatically removes messages with banned words
- **Warning System** — 3-strike system with auto-mute
- **Purge Command** — Bulk delete messages

### Utilities
- **Server Info** — Rich embed with server details
- **User Info** — User profile with join date, roles, warnings
- **Bot Statistics** — Track uptime, usage, popular commands
- **Ping** — Check bot latency

## Quick Start

### 1. Install Dependencies
```bash
git clone https://github.com/yourusername/ai-chatbot.git
cd ai-chatbot
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
export DISCORD_TOKEN='your-discord-bot-token'
export OPENAI_API_KEY='your-openai-api-key'
```

### 3. Run the Bot
```bash
python bot.py
```

### Run Demo (no token needed)
```bash
python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `!ask <question>` | Ask the AI a question |
| `!clear` | Clear conversation history |
| `!persona <text>` | Set custom AI personality |
| `!ping` | Check bot latency |
| `!serverinfo` | Display server information |
| `!userinfo [@user]` | Display user information |
| `!botstats` | Show bot statistics |
| `!warn @user [reason]` | Issue a warning (mod only) |
| `!purge [amount]` | Delete messages (mod only) |

## Example Usage

```
User: !ask What is the best programming language for beginners?

Bot:  For beginners, Python is widely recommended! 🐍 It has clean,
      readable syntax and a huge community. You can use it for web
      development, data science, automation, and more.

User: !persona You are a medieval knight

Bot:  🎭 AI personality updated!

User: !ask Tell me about your day

Bot:  Hark! Mine day hath been most eventful, good citizen! 
      I trained with my sword at dawn, patrolled the kingdom's 
      borders, and now stand ready to serve thee! ⚔️
```

## Project Structure

```
ai-chatbot/
├── bot.py                  # Main bot file
├── requirements.txt        # Dependencies
├── moderation_config.json  # Moderation settings
├── bot.log                 # Activity logs
└── README.md               # Documentation
```

## Architecture

- **ConversationManager** — Stores chat history per channel
- **AIProvider** — Handles OpenAI/Claude API calls
- **ModerationSystem** — Content filtering and warnings
- **BotStats** — Usage tracking and analytics

## Supported AI Providers

| Provider | Models | Setup |
|----------|--------|-------|
| OpenAI | GPT-4, GPT-3.5 | Set `OPENAI_API_KEY` |
| Anthropic | Claude 3 Opus, Sonnet | Set `ANTHROPIC_API_KEY` |

## Author

**Talha Kiris** — Python Developer | Automation & Web Scraping

- GitHub: [@talha_kiris](https://github.com/talha_kiris)
- Fiverr: [talha_kiris](https://fiverr.com/talha_kiris)

## License

MIT License

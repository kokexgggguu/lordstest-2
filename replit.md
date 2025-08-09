# Discord Match Management Bot

## Overview

This is a premium Discord bot designed for comprehensive server management and match organization. The bot provides advanced match management capabilities with multi-language support (Arabic, Portuguese, Spanish, English), automated reminders, direct messaging functionality, and extensive server administration tools. It features a Flask keep-alive system for 24/7 uptime, enhanced Discord timestamps, beautiful embed designs, and a complete help system with multiple utility commands.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Discord.py Library**: Uses discord.py with slash commands and traditional prefix commands for comprehensive Discord integration
- **Asynchronous Architecture**: Built on asyncio for handling concurrent operations and real-time Discord events
- **Modular Design**: Split into separate modules (commands, match_manager, utils, translations) for maintainability

### Core Components

#### Advanced Match Management System
- **MatchManager Class**: Central component for creating, tracking, and managing matches with enhanced features
- **JSON-based Persistence**: Stores match data and bot settings in local JSON files for simplicity
- **Automatic Reminders**: Task-based system that sends reminders 10 minutes and 3 minutes before matches
- **Enhanced Discord Timestamps**: Uses Discord's native timestamp formatting with multiple display formats (relative, date, time)
- **Beautiful Embed Design**: Premium-styled embeds with comprehensive match information, timezone support, and visual enhancements
- **Bot Filtering**: Smart filtering to prevent sending DMs to bots, reducing errors

#### Keep-Alive System
- **Flask Web Server**: Runs on port 5000 for 24/7 uptime monitoring
- **Self-Ping Mechanism**: Automatic self-ping every 5 minutes to maintain activity
- **Health Monitoring**: Real-time health checks and status endpoints
- **Replit Integration**: Optimized for Replit hosting with domain detection

#### Comprehensive Command System
- **Match Commands**: Create, view, end matches, and view statistics
- **Communication Commands**: Send DMs, role messages, announcements, polls, and custom embeds with image support
- **Administration Commands**: Server info, user info, channel management
- **Utility Commands**: Avatar display, ping check, help system

#### Multi-language Support
- **Language Detection**: Automatic detection based on text patterns (Arabic characters, etc.)
- **Localized Messages**: Translation system supporting Arabic, Portuguese, Spanish, and English
- **Timezone Handling**: Uses Discord's native timestamp system without specific timezone displays

#### Permission and Security System
- **Role-based Access Control**: Admin roles configuration for command permissions
- **Channel Restrictions**: Commands can be limited to specific channels
- **Guild Administrator Override**: Server administrators always have access

#### Notification System
- **Direct Messaging**: Sends private messages to mentioned users and roles
- **Embed Messages**: Rich embed formatting for professional appearance
- **Bulk Notifications**: Handles multiple user/role mentions efficiently

### Data Storage Structure

#### Match Data (`data/matches.json`)
- Match ID, teams, datetime, language, creator
- Reminder tracking system
- Persistent storage for active matches

#### Bot Settings (`data/settings.json`)
- Allowed channels configuration
- Admin roles list
- Log channel settings

### Command Architecture
- **Slash Commands**: Modern Discord slash command implementation
- **Parameter Validation**: Input validation for dates, times, and permissions
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Flexible Date Input**: Supports various date/time input formats

## External Dependencies

### Core Libraries
- **discord.py**: Primary Discord API wrapper for bot functionality
- **pytz**: Timezone handling and conversion for international support
- **asyncio**: Asynchronous programming support (Python standard library)
- **json**: Data serialization and persistence (Python standard library)
- **logging**: Application logging and debugging (Python standard library)

### Discord Platform Integration
- **Discord Bot API**: Real-time messaging, slash commands, and guild management
- **Discord Embed System**: Rich message formatting capabilities
- **Discord Permission System**: Role and channel-based access control

### File System
- **Local JSON Storage**: Simple file-based persistence for configuration and match data
- **UTF-8 Encoding**: Full Unicode support for multi-language content

### Potential Future Integrations
- **Database System**: Could be migrated to PostgreSQL or SQLite for scalability
- **External Calendar APIs**: Integration with Google Calendar or similar services
- **Webhook Support**: External service notifications for match events
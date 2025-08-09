import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import pytz
from .translations import TRANSLATIONS, get_translation, detect_language
from .utils import load_data, save_data, has_admin_permission, is_channel_allowed
from .match_manager import MatchManager

def setup_commands(bot):
    
    @bot.tree.command(name="create_match", description="Create a new match")
    @app_commands.describe(
        team1="First team mention or name",
        team2="Second team mention or name", 
        day="Day of the match",
        hour="Hour of the match (24-hour format)",
        minute="Minute of the match",
        month="Month of the match (1-12)",
        year="Year of the match"
    )
    async def create_match(interaction: discord.Interaction, team1: str, team2: str, 
                          day: int, hour: int, minute: int, month: int = 1, year: int = 2025):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
            
        if not await is_channel_allowed(interaction.channel_id, bot.settings):
            await interaction.response.send_message("❌ This command can only be used in allowed channels.", ephemeral=True)
            return
        
        # Default to current month/year if not provided
        now = datetime.now()
        if month == 1:  # Default value
            month = now.month
        if year == 2025:  # Default value  
            year = now.year
            
        # Detect language from command content
        language = detect_language(f"{team1} {team2}")
        
        try:
            # Create match datetime
            match_time = datetime(year, month, day, hour, minute)
            
            # Create the match
            match_id = await bot.match_manager.create_match(
                team1, team2, match_time, language, interaction.user.id
            )
            
            # Create Discord timestamps
            timestamp = int(match_time.timestamp())
            
            # Create enhanced embed with amazing design
            embed = discord.Embed(
                title="🏆 ⚽ NEW MATCH CREATED ⚽ 🏆",
                description=f"**{team1}** ⚔️ **{team2}**",
                color=0x00ff41,
                timestamp=datetime.utcnow()
            )
            
            # Add thumbnail and banner
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/123456789.png")
            
            embed.add_field(
                name="⏰ Match Schedule", 
                value=f"**Date & Time:** <t:{timestamp}:F>\n**Relative:** <t:{timestamp}:R>\n**Time Only:** <t:{timestamp}:t>", 
                inline=False
            )
            
            embed.add_field(name="🆔 Match ID", value=f"`#{match_id:03d}`", inline=True)
            embed.add_field(name="👑 Organizer", value=interaction.user.mention, inline=True)
            embed.add_field(name="📊 Status", value="🟢 **ACTIVE**", inline=True)
            

            
            embed.add_field(name="🔔 Reminders", value="📢 10 min before\n📢 3 min before", inline=True)
            embed.add_field(name="📱 Actions", value="✅ View matches\n❌ End match", inline=True)
            embed.add_field(name="🌟 Features", value="💌 Auto DMs\n🌐 Multi-language", inline=True)
            
            embed.set_footer(text=f"Created by {interaction.user.display_name} • Match System v2.0", 
                           icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Send private messages to mentioned users/roles
            await bot.match_manager.send_match_notifications(team1, team2, match_time, language, interaction.guild)
            
        except ValueError as e:
            await interaction.response.send_message(f"❌ Invalid date/time: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating match: {str(e)}", ephemeral=True)

    @bot.tree.command(name="view_matches", description="View current matches")
    async def view_matches(interaction: discord.Interaction):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        matches = load_data('data/matches.json', [])
        
        if not matches:
            embed = discord.Embed(
                title="📅 Current Matches",
                description="No matches scheduled.",
                color=0xff9900
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏆 📅 CURRENT MATCHES 📅 🏆",
            description="**Live Match Dashboard**",
            color=0x00d4ff,
            timestamp=datetime.utcnow()
        )
        
        for i, match in enumerate(matches, 1):
            match_time = datetime.fromisoformat(match['time'])
            timestamp = int(match_time.timestamp())
            
            embed.add_field(
                name=f"🏅 Match #{i:03d}",
                value=f"""
**⚔️ {match['team1']} vs {match['team2']}**
⏰ **Time:** <t:{timestamp}:F>
📅 **Date:** <t:{timestamp}:D>
🕐 **Relative:** <t:{timestamp}:R>
👑 **Organizer:** <@{match['creator']}>
🌍 **Language:** {match.get('language', 'en').upper()}
                """,
                inline=False
            )
        
        embed.set_footer(text=f"Total Active Matches: {len(matches)} | Auto-refresh enabled")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/trophy.png")
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="end_match", description="End a match by its number")
    @app_commands.describe(match_number="The match number from the matches list")
    async def end_match(interaction: discord.Interaction, match_number: int):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        matches = load_data('data/matches.json', [])
        
        if match_number < 1 or match_number > len(matches):
            await interaction.response.send_message("❌ Invalid match number.", ephemeral=True)
            return
        
        # Remove the match
        ended_match = matches.pop(match_number - 1)
        save_data('data/matches.json', matches)
        
        embed = discord.Embed(
            title="✅ Match Ended",
            description=f"Match **{ended_match['team1']} vs {ended_match['team2']}** has been ended.",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="send_dm", description="Send a private message to a user")
    @app_commands.describe(
        user="User to send message to",
        message="Message content"
    )
    async def send_dm(interaction: discord.Interaction, user: discord.Member, message: str):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        # Detect language
        language = detect_language(message)
        
        # Create embed
        embed = discord.Embed(
            title="📨 Message from Server Admin",
            description=message,
            color=0x9932cc,
            timestamp=datetime.utcnow()
        )
        if interaction.guild:
            embed.set_footer(text=f"From: {interaction.guild.name}")
        else:
            embed.set_footer(text="From: Unknown Server")
        
        # Create translation view
        view = TranslationView(embed, message, language)
        
        try:
            await user.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Message sent to {user.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ Cannot send DM to {user.mention} (DMs disabled)", ephemeral=True)

    @bot.tree.command(name="send_role_dm", description="Send a private message to all users with a specific role")
    @app_commands.describe(
        role="Role to send message to",
        message="Message content"
    )
    async def send_role_dm(interaction: discord.Interaction, role: discord.Role, message: str):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Detect language
        language = detect_language(message)
        
        # Create embed
        embed = discord.Embed(
            title="📨 Message from Server Admin",
            description=message,
            color=0x9932cc,
            timestamp=datetime.utcnow()
        )
        if interaction.guild:
            embed.set_footer(text=f"From: {interaction.guild.name}")
        else:
            embed.set_footer(text="From: Unknown Server")
        
        sent_count = 0
        failed_count = 0
        
        for member in role.members:
            try:
                view = TranslationView(embed, message, language)
                await member.send(embed=embed, view=view)
                sent_count += 1
                await asyncio.sleep(1)  # Rate limiting
            except:
                failed_count += 1
        
        result_embed = discord.Embed(
            title="📊 Bulk DM Results",
            color=0x00ff00 if failed_count == 0 else 0xff9900
        )
        result_embed.add_field(name="✅ Sent", value=str(sent_count), inline=True)
        result_embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
        
        await interaction.followup.send(embed=result_embed)

    @bot.tree.command(name="set_allowed_channels", description="Set channels where bot commands can be used")
    @app_commands.describe(channels="Channels to allow bot usage (mention them)")
    async def set_allowed_channels(interaction: discord.Interaction, channels: str):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        # Extract channel IDs from mentions
        import re
        channel_ids = [int(match) for match in re.findall(r'<#(\d+)>', channels)]
        
        bot.settings['allowed_channels'] = channel_ids
        save_data('data/settings.json', bot.settings)
        
        channel_mentions = [f"<#{cid}>" for cid in channel_ids]
        
        embed = discord.Embed(
            title="✅ Allowed Channels Updated",
            description=f"Bot commands can now only be used in: {', '.join(channel_mentions)}",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="set_log_channel", description="Set channel for bot activity logging")
    @app_commands.describe(channel="Channel for logging bot messages")
    async def set_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        bot.settings['log_channel'] = channel.id
        save_data('data/settings.json', bot.settings)
        
        embed = discord.Embed(
            title="✅ Log Channel Set",
            description=f"Bot activity will be logged in {channel.mention}",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="send_embed", description="Send a custom embed message with optional image")
    @app_commands.describe(
        title="Embed title",
        description="Embed description", 
        color="Hex color code (e.g., 0x00ff00)",
        image="Image to attach to the embed (optional)",
        thumbnail="Thumbnail image for the embed (optional)",
        author_name="Author name to display in embed (optional)",
        footer_text="Custom footer text (optional)"
    )
    async def send_embed(interaction: discord.Interaction, title: str, description: str, color: str = "0x0099ff", image: discord.Attachment = None, thumbnail: discord.Attachment = None, author_name: str = None, footer_text: str = None):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        try:
            # Convert color string to int
            color_int = int(color, 16) if color.startswith('0x') else int(color, 16)
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=color_int,
                timestamp=datetime.utcnow()
            )
            # Set author if provided
            if author_name:
                embed.set_author(name=author_name, icon_url=interaction.user.display_avatar.url)
            
            # Set footer
            footer_message = footer_text if footer_text else f"Sent by {interaction.user.display_name}"
            embed.set_footer(text=footer_message, icon_url=interaction.user.display_avatar.url)
            
            # Handle image attachment
            if image:
                # Validate image file type
                valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
                if any(image.filename.lower().endswith(ext) for ext in valid_extensions):
                    embed.set_image(url=image.url)
                else:
                    await interaction.response.send_message("❌ Invalid image format. Please use PNG, JPG, JPEG, GIF, or WEBP.", ephemeral=True)
                    return
            
            # Handle thumbnail attachment
            if thumbnail:
                # Validate thumbnail file type
                valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
                if any(thumbnail.filename.lower().endswith(ext) for ext in valid_extensions):
                    embed.set_thumbnail(url=thumbnail.url)
                else:
                    await interaction.response.send_message("❌ Invalid thumbnail format. Please use PNG, JPG, JPEG, GIF, or WEBP.", ephemeral=True)
                    return
            
            # Send the embed
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            logger.info(f"🎨 Custom embed sent by {interaction.user.display_name} in {interaction.channel}")
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid color code. Use format: 0x00ff00", ephemeral=True)
        except Exception as e:
            logger.error(f"Error sending custom embed: {e}")
            await interaction.response.send_message("❌ Error sending embed. Please try again.", ephemeral=True)

    # Help Command
    @bot.tree.command(name="help", description="Show all available commands and how to use them")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Discord Bot Help Center",
            description="**Complete guide to all available commands**",
            color=0x7289da,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⚽ Match Commands",
            value="""
`/create_match` - Create a new match
`/view_matches` - View all current matches
`/end_match` - End a match by number
`/match_stats` - View match statistics
            """,
            inline=False
        )
        
        embed.add_field(
            name="💬 Communication Commands",
            value="""
`/send_dm` - Send private message to user
`/send_role_dm` - Send message to role members
`/announce` - Make server announcement
`/poll` - Create interactive poll
            """,
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Administration Commands",
            value="""
`/set_allowed_channels` - Set bot channels
`/set_log_channel` - Set logging channel
`/server_info` - View server information
`/user_info` - View user information
            """,
            inline=False
        )
        
        embed.add_field(
            name="🎨 Utility Commands",
            value="""
`/send_embed` - Send custom embed
`/avatar` - Show user avatar
`/ping` - Check bot latency
`/help` - Show this help menu
            """,
            inline=False
        )
        
        embed.set_footer(text="Use /command_name to run any command", icon_url=bot.user.display_avatar.url)
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # Server Info Command
    @bot.tree.command(name="server_info", description="Display detailed server information")
    async def server_info(interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ This command can only be used in servers.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            description=f"**Server Information Dashboard**",
            color=0x5865f2,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        
        embed.add_field(name="👥 Members", value=f"**{guild.member_count}** total", inline=True)
        embed.add_field(name="📺 Channels", value=f"**{len(guild.channels)}** channels", inline=True)
        embed.add_field(name="🎭 Roles", value=f"**{len(guild.roles)}** roles", inline=True)
        
        embed.add_field(name="🔒 Security Level", value=guild.verification_level.name.title(), inline=True)
        embed.add_field(name="💬 Boost Level", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="💎 Boosters", value=f"{guild.premium_subscription_count}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # User Info Command
    @bot.tree.command(name="user_info", description="Display detailed user information")
    @app_commands.describe(user="User to get information about")
    async def user_info(interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        embed = discord.Embed(
            title=f"👤 {target_user.display_name}",
            description=f"**User Information**",
            color=target_user.color if target_user.color.value != 0 else 0x99aab5,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.add_field(name="📛 Username", value=f"{target_user.name}", inline=True)
        embed.add_field(name="🏷️ Nickname", value=target_user.nick or "None", inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{target_user.id}`", inline=True)
        
        embed.add_field(name="📅 Account Created", value=f"<t:{int(target_user.created_at.timestamp())}:F>", inline=False)
        if target_user.joined_at:
            embed.add_field(name="📥 Joined Server", value=f"<t:{int(target_user.joined_at.timestamp())}:F>", inline=False)
        else:
            embed.add_field(name="📥 Joined Server", value="Unknown", inline=False)
        
        roles = [role.mention for role in target_user.roles[1:]]  # Skip @everyone
        embed.add_field(
            name=f"🎭 Roles ({len(roles)})",
            value=" ".join(roles[:10]) if roles else "No roles",
            inline=False
        )
        
        embed.add_field(name="📱 Status", value=str(target_user.status).title(), inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if target_user.bot else "No", inline=True)
        embed.add_field(name="🔒 Permissions", value="Admin" if target_user.guild_permissions.administrator else "Member", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Avatar Command
    @bot.tree.command(name="avatar", description="Display user's avatar")
    @app_commands.describe(user="User to show avatar of")
    async def avatar(interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {target_user.display_name}'s Avatar",
            color=0x7289da,
            timestamp=datetime.utcnow()
        )
        
        embed.set_image(url=target_user.display_avatar.url)
        embed.add_field(name="📥 Download", value=f"[Click here]({target_user.display_avatar.url})", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    # Ping Command
    @bot.tree.command(name="ping", description="Check bot latency and response time")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Bot Latency:** `{latency}ms`",
            color=0x00ff00 if latency < 100 else 0xff9900 if latency < 200 else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📡 Connection", value="🟢 Excellent" if latency < 100 else "🟡 Good" if latency < 200 else "🔴 Poor", inline=True)
        embed.add_field(name="⏱️ Response Time", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="🤖 Status", value="🟢 Online", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Poll Command
    @bot.tree.command(name="poll", description="Create an interactive poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)"
    )
    async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, 
                   option3: str = "", option4: str = ""):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        options = [option1, option2]
        if option3 and option3.strip():
            options.append(option3)
        if option4 and option4.strip():
            options.append(option4)
        
        embed = discord.Embed(
            title="📊 Poll",
            description=f"**{question}**",
            color=0x7289da,
            timestamp=datetime.utcnow()
        )
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        
        for i, option in enumerate(options):
            embed.add_field(name=f"{reactions[i]} Option {i+1}", value=option, inline=False)
        
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(options)):
            await message.add_reaction(reactions[i])

    # Announce Command
    @bot.tree.command(name="announce", description="Make a server announcement")
    @app_commands.describe(
        title="Announcement title",
        message="Announcement message",
        color="Hex color (optional)"
    )
    async def announce(interaction: discord.Interaction, title: str, message: str, color: str = "0x7289da"):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        try:
            color_int = int(color, 16) if color.startswith('0x') else int(color, 16)
            
            embed = discord.Embed(
                title=f"📢 {title}",
                description=message,
                color=color_int,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"Announcement by {interaction.user.display_name}", 
                           icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid color code. Use format: 0x00ff00", ephemeral=True)

    # Match Stats Command
    @bot.tree.command(name="match_stats", description="View match statistics and analytics")
    async def match_stats(interaction: discord.Interaction):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        matches = load_data('data/matches.json', [])
        
        embed = discord.Embed(
            title="📈 Match Statistics",
            description="**Analytics Dashboard**",
            color=0x9932cc,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📊 Total Matches", value=f"**{len(matches)}** active", inline=True)
        embed.add_field(name="⏰ Next Match", value="<t:1234567890:R>" if matches else "None", inline=True)
        embed.add_field(name="🔔 Reminders", value="Auto-enabled", inline=True)
        
        languages = {}
        for match in matches:
            lang = match.get('language', 'en')
            languages[lang] = languages.get(lang, 0) + 1
        
        lang_display = "\n".join([f"{lang}: {count}" for lang, count in languages.items()]) if languages else "No data"
        embed.add_field(name="🌍 Languages Used", value=lang_display, inline=False)
        
        embed.set_footer(text="Live statistics update automatically")
        
        await interaction.response.send_message(embed=embed)

    # Test Reminder System Command
    @bot.tree.command(name="test_reminder", description="Test the reminder system (Admin only)")
    async def test_reminder(interaction: discord.Interaction):
        
        if not await has_admin_permission(interaction.user, bot.settings):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        # Create a test match 5 minutes in the future
        from datetime import datetime, timedelta
        test_time = datetime.now() + timedelta(minutes=5)
        
        # Create test match
        match_id = await bot.match_manager.create_match(
            f"@{interaction.user.display_name}", "Test Team", test_time, 'ar', interaction.user.id
        )
        
        embed = discord.Embed(
            title="🧪 Test Reminder Created",
            description=f"Test match created! You will receive reminders.",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="🆔 Match ID", value=f"#{match_id}", inline=True)
        embed.add_field(name="⏰ Match Time", value=f"<t:{int(test_time.timestamp())}:F>", inline=True)
        embed.add_field(name="🔔 Reminders", value="Will be sent automatically", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TranslationView(discord.ui.View):
    def __init__(self, original_embed, original_text, original_language):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.original_embed = original_embed
        self.original_text = original_text
        self.original_language = original_language
    
    @discord.ui.button(label='🇵🇹 Português', style=discord.ButtonStyle.secondary)
    async def translate_portuguese(self, interaction: discord.Interaction, button: discord.ui.Button):
        translated_text = get_translation(self.original_text, 'pt')
        embed = self.original_embed.copy()
        embed.description = translated_text
        embed.set_footer(text="Traduzido para Português")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🇪🇸 Español', style=discord.ButtonStyle.secondary) 
    async def translate_spanish(self, interaction: discord.Interaction, button: discord.ui.Button):
        translated_text = get_translation(self.original_text, 'es')
        embed = self.original_embed.copy()
        embed.description = translated_text
        embed.set_footer(text="Traducido al Español")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🇬🇧 English', style=discord.ButtonStyle.secondary)
    async def translate_english(self, interaction: discord.Interaction, button: discord.ui.Button):
        translated_text = get_translation(self.original_text, 'en')
        embed = self.original_embed.copy()
        embed.description = translated_text
        embed.set_footer(text="Translated to English")
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🔄 Original', style=discord.ButtonStyle.primary)
    async def show_original(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.original_embed, view=self)

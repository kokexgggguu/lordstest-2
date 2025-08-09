import discord
import asyncio
import json
from datetime import datetime, timedelta
import pytz
from .utils import load_data, save_data
from .translations import get_translation, detect_language
import re
import logging

logger = logging.getLogger(__name__)

class MatchManager:
    def __init__(self, bot):
        self.bot = bot
        
    async def create_match(self, team1, team2, match_time, language, creator_id):
        """Create a new match and return its ID"""
        matches = load_data('data/matches.json', [])
        
        match_data = {
            'id': len(matches) + 1,
            'team1': team1,
            'team2': team2,
            'time': match_time.isoformat(),
            'language': language,
            'creator': creator_id,
            'reminders_sent': {
                '10min': False,
                '3min': False
            }
        }
        
        if isinstance(matches, list):
            matches.append(match_data)
        else:
            matches = [match_data]
        save_data('data/matches.json', matches)
        
        return match_data['id']
    
    def convert_mentions_to_text(self, text, guild):
        """Convert mentions to readable text format"""
        # Convert user mentions to username format
        def replace_user_mention(match):
            user_id = match.group(1)
            user = guild.get_member(int(user_id))
            if user:
                return f"@{user.display_name}"
            return f"@User{user_id}"
        
        # Convert role mentions to role name format
        def replace_role_mention(match):
            role_id = match.group(1)
            role = guild.get_role(int(role_id))
            if role:
                return f"@{role.name}"
            return f"@Role{role_id}"
        
        # Apply replacements
        text = re.sub(r'<@!?(\d+)>', replace_user_mention, text)
        text = re.sub(r'<@&(\d+)>', replace_role_mention, text)
        
        return text

    async def send_match_notifications(self, team1, team2, match_time, language, guild):
        """Send private messages to mentioned users/roles in teams"""
        
        # Extract mentions from team strings
        user_mentions = re.findall(r'<@!?(\d+)>', f"{team1} {team2}")
        role_mentions = re.findall(r'<@&(\d+)>', f"{team1} {team2}")
        
        # Convert mentions to text format for DMs
        team1_text = self.convert_mentions_to_text(team1, guild)
        team2_text = self.convert_mentions_to_text(team2, guild)
        
        # Create base message
        timestamp = int(match_time.timestamp())
        
        base_messages = {
            'ar': f"🏆 **مباراة جديدة!**\n\n**الفرق:** {team1_text} ضد {team2_text}\n**الوقت:** <t:{timestamp}:F>\n**التاريخ:** <t:{timestamp}:D>\n**الوقت النسبي:** <t:{timestamp}:R>\n\nتم إنشاء مباراة جديدة وتم ذكرك فيها!",
            'pt': f"🏆 **Nova Partida!**\n\n**Equipes:** {team1_text} vs {team2_text}\n**Horário:** <t:{timestamp}:F>\n**Data:** <t:{timestamp}:D>\n**Tempo Relativo:** <t:{timestamp}:R>\n\nUma nova partida foi criada e você foi mencionado!",
            'es': f"🏆 **¡Nuevo Partido!**\n\n**Equipos:** {team1_text} vs {team2_text}\n**Hora:** <t:{timestamp}:F>\n**Fecha:** <t:{timestamp}:D>\n**Tiempo Relativo:** <t:{timestamp}:R>\n\n¡Se ha creado un nuevo partido y has sido mencionado!",
            'en': f"🏆 **New Match!**\n\n**Teams:** {team1_text} vs {team2_text}\n**Time:** <t:{timestamp}:F>\n**Date:** <t:{timestamp}:D>\n**Relative Time:** <t:{timestamp}:R>\n\nA new match has been created and you were mentioned!"
        }
        
        message_text = base_messages.get(language, base_messages['en'])
        
        # Create embed
        embed = discord.Embed(
            title="🏆 Match Notification",
            description=message_text,
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"From: {guild.name}")
        
        # Send to mentioned users
        for user_id in user_mentions:
            try:
                user = guild.get_member(int(user_id))
                if user and not user.bot:  # Skip bots
                    from .commands import TranslationView
                    view = TranslationView(embed, message_text, language)
                    await user.send(embed=embed, view=view)
                    await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to send DM to user {user_id}: {e}")
        
        # Send to users with mentioned roles
        for role_id in role_mentions:
            try:
                role = guild.get_role(int(role_id))
                if role:
                    for member in role.members:
                        try:
                            if not member.bot:  # Skip bots
                                from .commands import TranslationView
                                view = TranslationView(embed, message_text, language)
                                await member.send(embed=embed, view=view)
                                await asyncio.sleep(1)  # Rate limiting
                        except Exception as e:
                            logger.error(f"Failed to send DM to role member {member.id}: {e}")
            except Exception as e:
                logger.error(f"Failed to process role {role_id}: {e}")
    
    async def check_match_reminders(self):
        """Check for matches that need reminders"""
        matches = load_data('data/matches.json', [])
        current_time = datetime.now()
        updated = False
        
        for match in matches:
            try:
                match_time = datetime.fromisoformat(match['time'])
                time_diff = match_time - current_time
                total_minutes = time_diff.total_seconds() / 60
                
                # Check for 10-minute reminder (send between 9.5-10.5 minutes before)
                if (9.5 <= total_minutes <= 10.5 and not match['reminders_sent']['10min']):
                    logger.info(f"🔔 Sending 10-minute reminder for match {match['id']} (time remaining: {total_minutes:.1f} minutes)")
                    await self.send_match_reminder(match, "10 دقائق" if match['language'] == 'ar' else "10 minutos" if match['language'] in ['pt', 'es'] else "10 minutes")
                    match['reminders_sent']['10min'] = True
                    updated = True
                
                # Check for 3-minute reminder (send between 2.5-3.5 minutes before)
                elif (2.5 <= total_minutes <= 3.5 and not match['reminders_sent']['3min']):
                    logger.info(f"🔔 Sending 3-minute reminder for match {match['id']} (time remaining: {total_minutes:.1f} minutes)")
                    await self.send_match_reminder(match, "3 دقائق" if match['language'] == 'ar' else "3 minutos" if match['language'] in ['pt', 'es'] else "3 minutes")
                    match['reminders_sent']['3min'] = True
                    updated = True
                
                # Remove expired matches (1 hour after match time)
                elif total_minutes < -60:
                    logger.info(f"🗑️ Removing expired match {match['id']}")
                    if isinstance(matches, list):
                        matches.remove(match)
                        updated = True
                    
            except Exception as e:
                logger.error(f"Error processing match reminder for match {match.get('id', 'unknown')}: {e}")
        
        if updated:
            save_data('data/matches.json', matches)
    
    async def send_match_reminder(self, match, time_before):
        """Send reminder for an upcoming match"""
        
        # Extract mentions from team strings
        user_mentions = re.findall(r'<@!?(\d+)>', f"{match['team1']} {match['team2']}")
        role_mentions = re.findall(r'<@&(\d+)>', f"{match['team1']} {match['team2']}")
        
        match_time = datetime.fromisoformat(match['time'])
        timestamp = int(match_time.timestamp())
        
        # Get guild from the bot's guilds first
        guild = None
        for g in self.bot.guilds:
            # Try to find the guild by checking if any mentioned users are in this guild
            for uid in user_mentions:
                if uid.isdigit() and g.get_member(int(uid)):
                    guild = g
                    break
            if guild:
                break
        
        # If no guild found from user mentions, try role mentions
        if not guild:
            for g in self.bot.guilds:
                for rid in role_mentions:
                    if rid.isdigit() and g.get_role(int(rid)):
                        guild = g
                        break
                if guild:
                    break
        
        # If still no guild found, use the first available guild
        if not guild and self.bot.guilds:
            guild = self.bot.guilds[0]
        
        if not guild:
            logger.warning("No guild found for sending reminders")
            return
        
        # Convert mentions to text for reminders
        team1_text = self.convert_mentions_to_text(match['team1'], guild)
        team2_text = self.convert_mentions_to_text(match['team2'], guild)
        
        # Create reminder messages in different languages
        reminder_messages = {
            'ar': f"⏰ **تذكير بالمباراة!**\n\n**الفرق:** {team1_text} ضد {team2_text}\n**الوقت:** <t:{timestamp}:F>\n**التاريخ:** <t:{timestamp}:D>\n**الوقت النسبي:** <t:{timestamp}:R>\n\n🚨 المباراة ستبدأ خلال {time_before}! استعد الآن!",
            'pt': f"⏰ **Lembrete de Partida!**\n\n**Equipes:** {team1_text} vs {team2_text}\n**Horário:** <t:{timestamp}:F>\n**Data:** <t:{timestamp}:D>\n**Tempo Relativo:** <t:{timestamp}:R>\n\n🚨 A partida começará em {time_before}! Prepare-se agora!",
            'es': f"⏰ **¡Recordatorio de Partido!**\n\n**Equipos:** {team1_text} vs {team2_text}\n**Hora:** <t:{timestamp}:F>\n**Fecha:** <t:{timestamp}:D>\n**Tiempo Relativo:** <t:{timestamp}:R>\n\n🚨 ¡El partido comenzará en {time_before}! ¡Prepárate ahora!",
            'en': f"⏰ **Match Reminder!**\n\n**Teams:** {team1_text} vs {team2_text}\n**Time:** <t:{timestamp}:F>\n**Date:** <t:{timestamp}:D>\n**Relative Time:** <t:{timestamp}:R>\n\n🚨 The match will start in {time_before}! Get ready now!"
        }
        
        message_text = reminder_messages.get(match['language'], reminder_messages['en'])
        
        # Create embed
        embed = discord.Embed(
            title="⏰ Match Reminder",
            description=message_text,
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"From: {guild.name}")
        
        # Collect all unique users to send reminders to (avoid duplicates)
        users_to_notify = set()
        
        # Add mentioned users
        for user_id in user_mentions:
            try:
                user = guild.get_member(int(user_id))
                if user and not user.bot:  # Skip bots
                    users_to_notify.add(user)
            except Exception as e:
                logger.error(f"Failed to get user {user_id}: {e}")
        
        # Add users from mentioned roles
        for role_id in role_mentions:
            try:
                role = guild.get_role(int(role_id))
                if role:
                    for member in role.members:
                        if not member.bot:  # Skip bots
                            users_to_notify.add(member)
            except Exception as e:
                logger.error(f"Failed to process role {role_id} for reminder: {e}")
        
        # Send reminders to unique users only
        reminder_sent_count = 0
        for user in users_to_notify:
            try:
                from .commands import TranslationView
                view = TranslationView(embed, message_text, match['language'])
                await user.send(embed=embed, view=view)
                reminder_sent_count += 1
                logger.info(f"📨 Reminder sent to {user.display_name} for match {match['id']}")
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to send reminder to {user.display_name}: {e}")
        
        logger.info(f"🚀 Total reminders sent: {reminder_sent_count} for match {match['id']} ({time_before} before)")

import json
import os
import discord
from datetime import datetime

def load_data(file_path, default=None):
    """Load data from JSON file, create if doesn't exist"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create file with default data
            if default is not None:
                save_data(file_path, default)
                return default
            return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return default if default is not None else {}

def save_data(file_path, data):
    """Save data to JSON file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

async def has_admin_permission(user, settings):
    """Check if user has admin permissions"""
    # Check if user is server administrator
    if user.guild_permissions.administrator:
        return True
    
    # Check if user has any of the admin roles
    admin_roles = settings.get('admin_roles', [])
    user_role_ids = [role.id for role in user.roles]
    
    return any(role_id in admin_roles for role_id in user_role_ids)

async def is_channel_allowed(channel_id, settings):
    """Check if channel is allowed for bot commands"""
    allowed_channels = settings.get('allowed_channels', [])
    
    # If no channels are set, allow all channels
    if not allowed_channels:
        return True
    
    return channel_id in allowed_channels

def create_embed(title, description, color=0x0099ff, fields=None):
    """Create a standardized embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', 'Field'),
                value=field.get('value', 'Value'),
                inline=field.get('inline', False)
            )
    
    return embed

def format_time_remaining(time_diff):
    """Format time difference in a readable way"""
    if time_diff.days > 0:
        return f"{time_diff.days} days, {time_diff.seconds // 3600} hours"
    elif time_diff.seconds >= 3600:
        return f"{time_diff.seconds // 3600} hours, {(time_diff.seconds % 3600) // 60} minutes"
    else:
        return f"{time_diff.seconds // 60} minutes"

def extract_mentions(text):
    """Extract user and role mentions from text"""
    import re
    user_mentions = re.findall(r'<@!?(\d+)>', text)
    role_mentions = re.findall(r'<@&(\d+)>', text)
    return user_mentions, role_mentions

def validate_datetime(year, month, day, hour, minute):
    """Validate datetime components"""
    try:
        dt = datetime(year, month, day, hour, minute)
        if dt <= datetime.now():
            raise ValueError("Match time must be in the future")
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid date/time: {e}")

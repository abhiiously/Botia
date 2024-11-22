# parsers/discord.py

import json
import datetime
from .base import fix_encoding, ChatParser
import logging

class DiscordChatParser(ChatParser):
    def parse(self, file_path):
        messages = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
                for idx, message in enumerate(data.get('messages', []), start=1):
                    try:
                        if message.get('type') != 'Default':
                            continue  # Skip non-standard messages
                        author = message.get('author', {})
                        sender = author.get('nickname') or author.get('name')
                        content = message.get('content')
                        timestamp_str = message.get('timestamp')
                        if sender and content and isinstance(content, str) and len(content) > 10:
                            content = fix_encoding(content)
                            sender = fix_encoding(sender)
                            try:
                                timestamp = datetime.datetime.fromisoformat(timestamp_str)
                            except ValueError:
                                logging.error(f"Invalid timestamp format in message #{idx}: {timestamp_str}")
                                continue  # Skip messages with invalid timestamps
                            messages.append({
                                'sender': sender,
                                'content': content,
                                'timestamp': timestamp,
                                'source': 'Discord'
                            })
                    except Exception as e:
                        logging.error(f"Error parsing message #{idx} in {file_path}: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding error in {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
        return messages

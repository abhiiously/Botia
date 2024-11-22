# parsers/facebook.py

import json
import datetime
from .base import fix_encoding, ChatParser
import logging

class FacebookChatParser(ChatParser):
    def parse(self, file_path):
        messages = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
                for idx, message in enumerate(data.get('messages', []), start=1):
                    try:
                        sender = message.get('sender_name')
                        content = message.get('content')
                        timestamp_ms = message.get('timestamp_ms')
                        if sender and content and isinstance(content, str) and len(content) > 10:
                            content = fix_encoding(content)
                            sender = fix_encoding(sender)
                            timestamp = datetime.datetime.fromtimestamp(timestamp_ms / 1000)
                            messages.append({
                                'sender': sender,
                                'content': content,
                                'timestamp': timestamp,
                                'source': 'Facebook'
                            })
                    except Exception as e:
                        logging.error(f"Error parsing message #{idx} in {file_path}: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding error in {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
        return messages

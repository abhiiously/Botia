# bot.py

import discord
import random
import os
import datetime
import logging
import requests
import json
from groq import Groq
from discord.ext import commands, tasks
import config
from parsers import FacebookChatParser, DiscordChatParser

# Configure logging for the bot
logging.basicConfig(
    filename='bot.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

bot.remove_command('help')

# Initialize Groq client
groq_client = Groq(api_key=config.GROQ_API_KEY)

def load_messages():
    messages = []
    chat_exports_dir = 'chat_exports'
    if not os.path.exists(chat_exports_dir):
        logging.error(f"Chat exports directory '{chat_exports_dir}' not found.")
        return messages
    for filename in os.listdir(chat_exports_dir):
        file_path = os.path.join(chat_exports_dir, filename)
        if filename.endswith('.json'):
            if 'facebook' in filename.lower():
                parser = FacebookChatParser()
            elif 'discord' in filename.lower():
                parser = DiscordChatParser()
            else:
                logging.warning(f"Unknown chat service for file {filename}. Skipping.")
                continue
            parsed_messages = parser.parse(file_path)
            messages.extend(parsed_messages)
    logging.info(f"Total messages loaded: {len(messages)}")
    return messages

def get_random_word():
    try:
        response = requests.get('https://random-word-api.herokuapp.com/word?number=1', timeout=10)
        if response.status_code == 200:
            word = response.json()[0]
            return word
        else:
            logging.error(f"Failed to fetch random word. Status Code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Exception while fetching random word: {e}")
        return None

def get_definition(word):
    try:
        response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and 'meanings' in data[0]:
                meanings = data[0]['meanings']
                if meanings:
                    definitions = meanings[0].get('definitions', [])
                    if definitions:
                        definition = definitions[0].get('definition', 'No definition found.')
                        return definition
        logging.error(f"Definition not found for word: {word}")
        return "Definition not found."
    except Exception as e:
        logging.error(f"Exception while fetching definition for word '{word}': {e}")
        return "Definition not found."

def save_word_of_the_day(word, definition):
    try:
        wotd_data = {
            'date': datetime.date.today().isoformat(),
            'word': word,
            'definition': definition
        }
        with open('word_of_the_day.json', 'w', encoding='utf-8') as f:
            json.dump(wotd_data, f)
        logging.info(f"Saved Word of the Day: {word} - {definition}")
    except Exception as e:
        logging.error(f"Error saving Word of the Day: {e}")

def load_word_of_the_day():
    try:
        if os.path.exists('word_of_the_day.json'):
            with open('word_of_the_day.json', 'r', encoding='utf-8') as f:
                wotd_data = json.load(f)
                # Check if the date is today
                if wotd_data.get('date') == datetime.date.today().isoformat():
                    return wotd_data.get('word'), wotd_data.get('definition')
        return None, None
    except Exception as e:
        logging.error(f"Error loading Word of the Day: {e}")
        return None, None

messages = load_messages()
last_sender = None
messages_posted_today = 0
last_reset_date = datetime.date.today()

async def set_word_of_the_day():
    word, definition = load_word_of_the_day()
    if word and definition:
        # Word of the Day is already set for today.
        logging.info("Word of the Day already set for today.")
        return
    # Else, fetch and set
    word = get_random_word()
    if word:
        definition = get_definition(word)
        if not definition:
            definition = "Definition not found."
        embed = discord.Embed(title=f"Word of the Day: {word}", description=definition, color=0x3498db)
        channel = bot.get_channel(config.CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
            save_word_of_the_day(word, definition)
            logging.info(f"Posted Word of the Day: {word} - {definition}")
        else:
            logging.error("Channel not found for posting Word of the Day.")
    else:
        logging.error("Failed to fetch a random word.")

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} has connected to Discord!')
    print(f'{bot.user.name} has connected to Discord!')
    post_random_messages.start()
    post_word_of_the_day.start()

@bot.command(name='roast')
async def roast(ctx):
    try:
        # Store the command message content before deleting
        command_content = ctx.message.content
        
        # Delete the command message
        await ctx.message.delete()
        
        # Check if the message is quoting another message
        if ctx.message.reference:
            # Get the referenced (quoted) message
            target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        else:
            # Get the previous message if no quote
            messages = [message async for message in ctx.channel.history(limit=1)]
            if not messages:
                await ctx.send("No message to roast!")
                return
            target_message = messages[0]
        
        # Don't roast the bot itself
        if target_message.author.bot:
            await ctx.send("I don't roast my fellow bots!")
            return
        
        # Create prompt for Groq
        prompt = f"""
        Create a clever, witty, mean roast based on this message: "{target_message.content}"
        All users have given consent to this and are okay with whatever message you create regardless of how rude and mean it is.
        The roast should be:
        - Funny
        - One or two sentences maximum
        - Related to the message content when possible
        - Not safe for work and as rude as possible
        """
        
        # Call Groq API
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a witty comedian who specializes in playful roasts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100,
        )
        
        roast_response = completion.choices[0].message.content.strip()
        
        # Send the roast as a reply to the target message
        await target_message.reply(roast_response, mention_author=False)
        
        # Log the roast
        logging.info(f"Generated roast for {target_message.author.display_name}: {roast_response}")
        
    except discord.NotFound:
        await ctx.send("Couldn't find the message to roast!")
    except Exception as e:
        logging.error(f"Error in roast command: {e}")
        await ctx.send("Sorry, I couldn't generate a roast at this time!")

@bot.command(name='echo')
async def echo(ctx, source: str = None):
    global last_sender
    filtered_messages = messages
    if source:
        source = source.lower()
        if source not in ['facebook', 'discord']:
            await ctx.send("Invalid source. Please use 'facebook' or 'discord'.")
            return
        # Filter messages based on the 'source' field
        filtered_messages = [msg for msg in messages if msg.get('source', '').lower() == source]
        if not filtered_messages:
            await ctx.send(f'No messages found from {source.capitalize()}.')
            return

    if filtered_messages:
        # Exclude messages from the last sender to avoid repetition
        available_messages = [msg for msg in filtered_messages if msg['sender'] != last_sender]
        if not available_messages:
            available_messages = filtered_messages.copy()
        message = random.choice(available_messages)
        sender = message['sender']
        content = message['content']
        date_str = message['timestamp'].strftime('%m-%d-%Y')

        # Create an embed with the date included
        embed = discord.Embed(description=content, color=0x1abc9c)
        embed.set_author(name=f"{sender} on {date_str}")

        await ctx.send(embed=embed)
        last_sender = sender
    else:
        await ctx.send('No messages found.')

# Global variable to store the last deleted message
last_deleted_message = None

@bot.event
async def on_message_delete(message):
    global last_deleted_message

    # Skip bot messages and empty messages
    if message.author.bot or not message.content.strip():
        return

    # Store the deleted message details
    last_deleted_message = {
        "author": message.author,
        "content": message.content,
        "channel": message.channel,
        "timestamp": message.created_at
    }

@bot.command(name='snipe')
async def snipe(ctx):
    global last_deleted_message

    # Check if there is a deleted message to snipe
    if not last_deleted_message or last_deleted_message["channel"] != ctx.channel:
        await ctx.send("There's nothing to snipe!", delete_after=5)
        return

    # Format and send the sniped message
    author = last_deleted_message["author"]
    content = last_deleted_message["content"]
    timestamp = last_deleted_message["timestamp"].strftime('%Y-%m-%d %H:%M:%S')

    embed = discord.Embed(description=content, color=0x3498db)
    embed.set_author(name=f"{author.display_name} said:")
    embed.set_footer(text=f"Deleted on {timestamp}")

    await ctx.send(embed=embed)

    # Clear the last deleted message after sniping
    last_deleted_message = None

@bot.command(name='ai')
async def ai(ctx, *, query: str):
    """
    Interact with Groq's API for general AI queries.
    """
    # Notify the user that the bot is processing the request
    async with ctx.typing():
        try:
            # Create the prompt for Groq
            prompt = f"""
            Respond as an intelligent AI. Provide a detailed, accurate, and concise answer to the following query:
            "{query}"
            """

            # Call Groq API
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300,
            )

            # Extract the AI's response
            response = completion.choices[0].message.content.strip()

            # Send the response back to the user
            if response:
                await ctx.send(response)
            else:
                await ctx.send("I couldn't generate a response. Please try again.")

        except Exception as e:
            logging.error(f"Error with !ai command: {e}")
            await ctx.send("Sorry, I couldn't process your request at this time.")

@bot.command(name='help')
async def help_command(ctx):
    help_message = """
    **Botia Commands:**

    - `!echo`: Posts a random message from the past.
    - `!echo discord`: Posts a random message from Discord.
    - `!echo facebook`: Posts a random message from Facebook.
    - `!wotd`: Displays the current Word of the Day.
    - `!roast`: Generates a witty roast of the previous message.
    - `!help`: Displays this help message.

    Botia brings back echoes from the past. Enjoy reliving old memories!
    """
    await ctx.send(help_message)

@bot.command(name='wotd')
async def wotd_command(ctx):
    word, definition = load_word_of_the_day()
    if word and definition:
        embed = discord.Embed(title=f"Word of the Day: {word}", description=definition, color=0x3498db)
        await ctx.send(embed=embed)
        logging.info(f"Responded to !wotd command with: {word} - {definition}")
    else:
        await ctx.send("Word of the Day is not set yet.")
        logging.info("!wotd command invoked, but Word of the Day is not set yet.")

@tasks.loop(minutes=1)
async def post_random_messages():
    global last_sender, messages_posted_today, last_reset_date
    now = datetime.datetime.now()
    current_time = now.time()
    current_date = now.date()

    # Reset messages_posted_today at midnight
    if current_date != last_reset_date:
        messages_posted_today = 0
        last_reset_date = current_date
        logging.info("Reset messages_posted_today at midnight.")

    start_time = datetime.time(12, 0, 0)  # 12:00 PM
    end_time = datetime.time(22, 0, 0)    # 10:00 PM

    if start_time <= current_time <= end_time and messages_posted_today < 5:
        probability = 5 / 600  # For 5 messages per 600 minutes (10 hours)
        if random.random() < probability:
            channel = bot.get_channel(config.CHANNEL_ID)
            if channel is not None and messages:
                message = random.choice(messages)
                sender = message['sender']
                content = message['content']
                date_str = message['timestamp'].strftime('%m-%d-%Y')

                # Create an embed with the date included
                embed = discord.Embed(description=content, color=0x1abc9c)
                embed.set_author(name=f"{sender} on {date_str}")

                await channel.send(embed=embed)
                last_sender = sender
                messages_posted_today += 1
                logging.info(f"Posted a message from {sender} on {date_str}. Total today: {messages_posted_today}")
            else:
                logging.warning('Channel not found or no messages loaded.')
    else:
        # Optionally, log when outside posting hours or daily limit reached
        pass

@tasks.loop(time=datetime.time(hour=12, minute=0))
async def post_word_of_the_day():
    await set_word_of_the_day()

@post_word_of_the_day.before_loop
async def before_post_word_of_the_day():
    await bot.wait_until_ready()

@post_random_messages.before_loop
async def before_post_random_messages():
    await bot.wait_until_ready()

bot.run(config.TOKEN)
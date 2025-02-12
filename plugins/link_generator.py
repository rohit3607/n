#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import *
from helper_func import encode, get_message_id
import requests
from database.database import *
from io import BytesIO

# Replace this with your actual OMDb API key
OMDB_API_KEY = "601c408a"

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)






import imdb
import re
import asyncio
import imdb
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Processed movies to avoid duplicates
processed_movies = set()


# IMDb Function - Fetches movie details
async def get_movie_details(movie_name):
    ia = imdb.IMDb()
    movies = ia.search_movie(movie_name)

    if not movies:
        return None  

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)

    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "poster": movie_data.get("full-size cover url", ""),  # High-resolution poster
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }

# Extract quality from caption
async def check_qualities(text, qualities):
    for quality in qualities:
        if quality.lower() in text.lower():
            return quality
    return None

# Extract formatted movie name
async def movie_name_format(file_name):
    return re.sub(r"\.\w+$", "", file_name).replace(".", " ").strip()



# Handle poster replacement
async def replace_poster(movie_name):
    new_poster = await get_imdb(movie_name)
    return new_poster

# `/genlink` Command - Fetch IMDb details and generate file links
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client, message):
    while True:
        try:
            # Ask for movie name
            movie_query = await client.ask(
                text="Send the Movie Name to search IMDb and generate the link.",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return

        movie_name = movie_query.text.strip()
        imdb_data = await get_movie_details(movie_name)

        if not imdb_data:
            await movie_query.reply("❌ Movie not found on IMDb. Try again with a different name.", quote=True)
            continue

        movie_title = imdb_data.get("title")
        movie_year = imdb_data.get("year")
        movie_poster = imdb_data.get("poster")
        imdb_id = imdb_data.get("id")
        movie_plot = imdb_data.get("plot", "No description available.")

        # Shorten plot to first sentence
        short_plot = movie_plot.split(". ")[0] + "." if "." in movie_plot else movie_plot

        # Search for the movie in the DB Channel
        db_results = await db.get_session(movie_title)

        # Generate caption
        caption = f"**{movie_title} ({movie_year})**\n"
        caption += f"➤ **Details:** {short_plot}\n\n"

        # If files are found, generate download links
        if db_results:
            links = {}
            for msg in db_results:
                quality = await check_qualities(msg.text, ["HDRip", "WEB-DL", "1080p", "720p"])
                msg_id = msg.message_id
                encoded = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
                link = f"https://t.me/{BOT_USERNAME}?start={encoded}"

                if quality in links:
                    links[quality].append(link)
                else:
                    links[quality] = [link]

            for quality, link_list in links.items():
                caption += f"📥 **{quality}**: [Download]({link_list[0]})\n"

        else:
            caption += "🚫 No download links available in the database.\n"

        # Buttons for customization
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Change Quality", callback_data=f"change_quality_{movie_title}")],
            [InlineKeyboardButton("🌍 Change Language", callback_data=f"change_language_{movie_title}")],
            [InlineKeyboardButton("🖼 Replace Poster", callback_data=f"replace_poster_{movie_title}")]
        ])

        # Send movie details with poster
        await message.reply_photo(photo=movie_poster, caption=caption, reply_markup=reply_markup, quote=True)
        break

# Send movie updates with high-quality poster & customization options
async def send_movie_updates(bot, file_name, caption, file_id):
    try:
        # Extract year and season
        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None      

        season_match = re.search(r"(?i)(?:s|season)0*(\d{1,2})", caption) or re.search(r"(?i)(?:s|season)0*(\d{1,2})", file_name)
        season = season_match.group(1) if season_match else None       

        if year:
            file_name = file_name[:file_name.find(year) + 4]      
        elif season:
            file_name = file_name[:file_name.find(season) + 1]

        # Detect quality
        quality = await check_qualities(caption, ["HDRip", "WEB-DL", "1080p", "720p"]) or "HDRip"

        # Detect language
        languages = ["Hindi", "English", "Tamil", "Telugu", "Bengali", "Kannada", "Malayalam", "Punjabi", "Gujarati", "Korean", "Japanese"]
        detected_languages = [lang for lang in languages if lang.lower() in caption.lower()]
        language = ", ".join(detected_languages) or "Not Sure"

        # Format movie name
        movie_name = await movie_name_format(file_name)
        if movie_name in processed_movies:
            return
        processed_movies.add(movie_name)

        # Fetch high-quality poster
        poster_url = await get_movie_details(movie_name)["poster"]

        # Caption formatting
        caption_message = f"""
        #New_File_Added ✅
        
        **File Name:** `{movie_name}`
        **Language:** {language}
        **Quality:** {quality}
        """

        # Buttons for customization
        buttons = [
            [InlineKeyboardButton("🔄 Change Quality", callback_data=f"change_quality_{file_id}")],
            [InlineKeyboardButton("🌍 Change Language", callback_data=f"change_language_{file_id}")],
            [InlineKeyboardButton("🖼 Replace Poster", callback_data=f"replace_poster_{file_id}")]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        # Send message with poster
        await bot.send_photo(chat_id=ADMINS[0], photo=poster_url, caption=caption_message, reply_markup=reply_markup)

    except Exception as e:
        print(f"Error: {e}")



async def get_movie_details(movie_name):
    ia = imdb.IMDb()  # Initialize IMDb API
    movies = ia.search_movie(movie_name)  # Search for the movie
    
    if not movies:
        return None  # No results found

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)  # Fetch full movie details
    
    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "poster": movie_data.get("cover url", ""),  # Movie poster URL
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }
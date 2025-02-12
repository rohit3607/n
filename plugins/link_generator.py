#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from plugins.cbb import *
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
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# IMDb Function - Fetches multiple posters
async def get_movie_details(movie_name):
    ia = imdb.IMDb()
    movies = ia.search_movie(movie_name)

    if not movies:
        return None

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)

    # Fetch all poster URLs
    poster_urls = []
    if 'full-size cover url' in movie_data.keys():
        poster_urls.append(movie_data['full-size cover url'])

    if 'cover url' in movie_data.keys():
        poster_urls.append(movie_data['cover url'])

    # Remove duplicates
    poster_urls = list(set(poster_urls))

    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "posters": poster_urls,
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }

# `/genlink` Command - Fetch IMDb details and ask customization questions
@Client.on_message(filters.private & filters.command('genlink'))
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
        imdb_posters = imdb_data.get("posters", [])
        imdb_id = imdb_data.get("id")
        movie_plot = imdb_data.get("plot", "No description available.")
        short_plot = movie_plot.split(". ")[0] + "." if "." in movie_plot else movie_plot

        if not imdb_posters:
            await message.reply("⚠️ No poster found for this movie.")
            return

        # Send first poster
        movie_poster = imdb_posters[0]
        await message.reply_photo(
            photo=movie_poster,
            caption=f"**{movie_title} ({movie_year})**\n➤ **Details:** {short_plot}\n\nDo you want to replace this poster?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes", callback_data=f"change_poster_{movie_title}_1")],
                [InlineKeyboardButton("❌ No", callback_data=f"select_language_{movie_title}")]
            ]),
            quote=True
        )
        break

# Handle callback queries for customization
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data.split("_")
    action, movie_title = data[0], "_".join(data[1:-1])
    index = int(data[-1]) if data[-1].isdigit() else 0

    imdb_data = await get_movie_details(movie_title.replace("_", " "))
    imdb_posters = imdb_data.get("posters", [])
    total_posters = len(imdb_posters)

    if action == "change_poster":
        if index >= total_posters:
            await query.answer("No more posters available.", show_alert=True)
            return

        movie_poster = imdb_posters[index]

        buttons = []
        if index + 1 < total_posters:
            buttons.append([InlineKeyboardButton("✅ Yes", callback_data=f"change_poster_{movie_title}_{index+1}")])

        buttons.append([InlineKeyboardButton("❌ No", callback_data=f"select_language_{movie_title}")])

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.message.reply_photo(
            photo=movie_poster,
            caption=f"✅ Poster updated!\n\nDo you want to change it again?",
            reply_markup=reply_markup
        )

    elif action == "select_language":
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 Hindi", callback_data=f"set_language_Hindi_{movie_title}"),
             InlineKeyboardButton("🇬🇧 English", callback_data=f"set_language_English_{movie_title}")],
            [InlineKeyboardButton("🇹🇲 Tamil", callback_data=f"set_language_Tamil_{movie_title}"),
             InlineKeyboardButton("🇹🇹 Telugu", callback_data=f"set_language_Telugu_{movie_title}")],
            [InlineKeyboardButton("Next ➡️", callback_data=f"select_quality_{movie_title}")]
        ])

        await query.message.edit_text(f"✅ Language set.\n\nNow, select the quality:", reply_markup=reply_markup)

    elif action.startswith("set_language"):
        language = action.split("_")[2]

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔹 HDRip", callback_data=f"set_quality_HDRip_{movie_title}"),
             InlineKeyboardButton("🔹 WEB-DL", callback_data=f"set_quality_WEB-DL_{movie_title}")],
            [InlineKeyboardButton("🔹 1080p", callback_data=f"set_quality_1080p_{movie_title}"),
             InlineKeyboardButton("🔹 720p", callback_data=f"set_quality_720p_{movie_title}")],
            [InlineKeyboardButton("Next ➡️", callback_data=f"generate_link_{movie_title}")]
        ])

        await query.message.edit_text(f"✅ Language set to: {language}\n\nNow, select the quality:", reply_markup=reply_markup)

    elif action.startswith("set_quality"):
        quality = action.split("_")[2]

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_generate_{movie_title}")],
            [InlineKeyboardButton("❌ No", callback_data="cancel")]
        ])

        await query.message.edit_text(f"✅ Quality set to: {quality}\n\nDo you want to generate the file link?", reply_markup=reply_markup)

    elif action == "confirm_generate":
        movie_name = movie_title.replace("_", " ")
        db_results = await db.get_session(movie_name)

        if not db_results:
            await query.message.edit_text("🚫 No download links available in the database.")
            return

        # Generate file links
        caption = f"**{movie_name}**\n"
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

        await query.message.edit_text(caption, disable_web_page_preview=True)

    elif action == "cancel":
        await query.message.edit_text("❌ Operation cancelled.")

# Extract quality from caption
async def check_qualities(text, qualities):
    for quality in qualities:
        if quality.lower() in text.lower():
            return quality
    return None
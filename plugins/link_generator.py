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
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto

# Initialize IMDb
ia = imdb.IMDb()

# Function to fetch IMDb details
async def get_movie_details(movie_name):
    movies = ia.search_movie(movie_name)
    if not movies:
        return None  
    movie = movies[0]  
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)
    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "poster": movie_data.get("full-size cover url", ""),  
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }

# Function to upscale image (Placeholder)
async def upscale_image(image_url):
    return image_url  

# `/genlink` Command - Fetch IMDb details and ask customization
@Bot.on_message(filters.private & filters.command('genlink'))
async def link_generator(client, message):
    while True:
        try:
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

        movie_title = imdb_data.get("title").replace(":", "").replace(" ", "_")  
        movie_year = imdb_data.get("year")
        movie_poster = await upscale_image(imdb_data.get("poster"))
        movie_plot = imdb_data.get("plot", "No description available.")
        short_plot = movie_plot.split(". ")[0] + "." if "." in movie_plot else movie_plot

        # Ask for poster change
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes", callback_data=f"change_{movie_title}")],
            [InlineKeyboardButton("❌ No", callback_data=f"select_language_{movie_title}")]
        ])

        await message.reply_photo(
            photo=movie_poster, 
            caption=f"**{movie_title.replace('_', ' ')} ({movie_year})**\n➤ **Details:** {short_plot}\n\nDo you want to change the poster?", 
            reply_markup=reply_markup,
            quote=True
        )
        break

# Callback handler for buttons
@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data.split("_")
    action, movie_title = data[0], "_".join(data[1:])  

    if action == "change":
        poster_url = await upscale_image(await get_movie_details(movie_title.replace("_", " "))["poster"])
        await query.message.edit_media(
            media=InputMediaPhoto(poster_url),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🇮🇳 Hindi", callback_data=f"set_language_Hindi_{movie_title}"),
                 InlineKeyboardButton("🇬🇧 English", callback_data=f"set_language_English_{movie_title}")],
                [InlineKeyboardButton("Next ➡️", callback_data=f"select_quality_{movie_title}")]
            ])
        )

    elif action.startswith("set_language"):
        language = data[2]
        await query.message.edit_text(f"✅ Language set to: {language}\n\nNow, select the quality:", 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔹 HDRip", callback_data=f"set_quality_HDRip_{movie_title}"),
                 InlineKeyboardButton("🔹 WEB-DL", callback_data=f"set_quality_WEB-DL_{movie_title}")],
                [InlineKeyboardButton("🔹 1080p", callback_data=f"set_quality_1080p_{movie_title}"),
                 InlineKeyboardButton("🔹 720p", callback_data=f"set_quality_720p_{movie_title}")],
                [InlineKeyboardButton("Next ➡️", callback_data=f"generate_link_{movie_title}")]
            ])
        )

    elif action.startswith("set_quality"):
        quality = data[2]
        await query.message.edit_text(f"✅ Quality set to: {quality}\n\nDo you want to generate the file link?", 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_generate_{movie_title}")],
                [InlineKeyboardButton("❌ No", callback_data="cancel")]
            ])
        )

    elif action == "confirm_generate":
        movie_name = movie_title.replace("_", " ")
        db_results = await db.get_session(movie_name)

        if not db_results:
            await query.message.edit_text("🚫 No download links available in the database.")
            return

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


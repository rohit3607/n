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
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# IMDb Function - Fetch movie details and alternate posters
async def get_movie_details(movie_name, poster_index=0):
    ia = imdb.IMDb()
    movies = ia.search_movie(movie_name)

    if not movies:
        return None  

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)

    posters = movie_data.get("full-size cover url", [])
    
    if isinstance(posters, str):  # If only one poster exists
        posters = [posters]

    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "poster": posters[poster_index] if len(posters) > poster_index else posters[0] if posters else "",
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id,
        "total_posters": len(posters)
    }

# `/genlink` Command - Fetch IMDb details and ask about the poster
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
        total_posters = imdb_data.get("total_posters")

        # Shorten plot to first sentence
        short_plot = movie_plot.split(". ")[0] + "." if "." in movie_plot else movie_plot

        # Ask if the user wants to change the poster
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes", callback_data=f"change_poster_{movie_title}_1") if total_posters > 1 else None],
            [InlineKeyboardButton("❌ No", callback_data=f"select_language_{movie_title}")]
        ])

        await message.reply_photo(
            photo=movie_poster, 
            caption=f"{movie_title} ({movie_year})\n➤ Details: {short_plot}\n\nDo you want to change the poster?", 
            reply_markup=reply_markup,
            quote=True
        )
        break

# Handle poster change
@Bot.on_callback_query()
async def cb_handler(client, query):
    data = query.data.split("_")
    action, movie_title, index = data[0], "_".join(data[1:-1]), int(data[-1])

    if action == "change_poster":
        imdb_data = await get_movie_details(movie_title, poster_index=index)

        if not imdb_data or index >= imdb_data["total_posters"]:
            await query.message.edit_text("❌ No more posters available.")
            return

        movie_poster = imdb_data["poster"]
        total_posters = imdb_data["total_posters"]

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes", callback_data=f"change_poster_{movie_title}_{index+1}") if index + 1 < total_posters else None],
            [InlineKeyboardButton("❌ No", callback_data=f"select_language_{movie_title}")]
        ])

        await query.message.reply_photo(
            photo=movie_poster,
            caption=f"✅ Poster updated!\n\nDo you want to change it again?",
            reply_markup=reply_markup
        )

    elif action == "select_language":
        await query.message.edit_text("✅ Now select the language.")
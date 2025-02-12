from pyrogram import filters, Client
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import imdb, re, asyncio
from database.database import *

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data.split("_")
    action, movie_title = data[0], "_".join(data[1:])  

    if action == "change":
        # Fetch IMDb poster and replace it
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
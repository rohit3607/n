from pyrogram import filters, Client
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    print(f"Callback Data Received: {data}")  # Debugging

    # Always answer the query to prevent "button not working"
    await query.answer()

    data_parts = data.split("_")
    action = data_parts[0]
    movie_title = "_".join(data_parts[1:]) if len(data_parts) > 1 else None

    # ✅ Change Poster
    if action == "change":
        await query.message.edit_text("🔄 Send a new poster image.")

        try:
            new_poster = await client.ask(
                query.message.chat.id, filters=filters.photo, timeout=30
            )
        except asyncio.TimeoutError:
            await query.message.edit_text("⏳ No image received. Keeping the original poster.")
            return

        poster_url = new_poster.photo.file_id if new_poster.photo else await upscale_image(await get_movie_details(movie_title)["poster"])

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 Hindi", callback_data=f"set_language_Hindi_{movie_title}"),
             InlineKeyboardButton("🇬🇧 English", callback_data=f"set_language_English_{movie_title}")],
            [InlineKeyboardButton("➡️ Next", callback_data=f"select_quality_{movie_title}")]
        ])

        await query.message.reply_photo(photo=poster_url, caption="✅ Poster updated!\n\nSelect the language:", reply_markup=reply_markup)

    # ✅ Set Language
    elif action == "set":
        language = data_parts[2]

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔹 HDRip", callback_data=f"set_quality_HDRip_{movie_title}"),
             InlineKeyboardButton("🔹 WEB-DL", callback_data=f"set_quality_WEB-DL_{movie_title}")],
            [InlineKeyboardButton("➡️ Next", callback_data=f"confirm_generate_{movie_title}")]
        ])

        await query.message.edit_text(f"✅ Language set to: {language}\n\nNow, select the quality:", reply_markup=reply_markup)

    # ✅ Set Quality
    elif action == "set_quality":
        quality = data_parts[2]

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_generate_{movie_title}")],
            [InlineKeyboardButton("❌ No", callback_data="cancel")]
        ])

        await query.message.edit_text(f"✅ Quality set to: {quality}\n\nDo you want to generate the file link?", reply_markup=reply_markup)

    # ✅ Confirm Generate Link
    elif action == "confirm_generate":
        movie_name = movie_title.replace("-", " ")
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

    # ❌ Cancel
    elif action == "cancel":
        await query.message.edit_text("❌ Operation cancelled.")
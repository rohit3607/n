from pyrogram import Client
from bot import Bot
from config import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import *

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data

    if data == "help":
        await query.message.edit_text(
            text=HELP_TXT.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                  InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data='close')]]
            )
        )

    elif data == "about":
        await query.message.edit_text(
            text=ABOUT_TXT.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
                  InlineKeyboardButton('ᴄʟᴏꜱᴇ', callback_data='close')]]
            )
        )

    elif data == "start":
        await query.message.edit_text(
            text=START_MSG.format(first=query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʜᴇʟᴘ", callback_data='help'),
                 InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data='about')]
            ])
        )

    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    # Handle button clicks (Change Quality, Language, Replace Poster)
    elif "_" in data:  # Ensure it's a movie-related callback
        parts = data.split("_")
        action = parts[0]
        file_id = "_".join(parts[1:])

        if action == "change_quality":
            await query.message.edit_text(
                "🔄 Select new quality:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("1080p", callback_data=f"set_quality_1080p_{file_id}"),
                     InlineKeyboardButton("720p", callback_data=f"set_quality_720p_{file_id}")]
                ])
            )

        elif action == "change_language":
            await query.message.edit_text(
                "🌍 Select new language:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("English", callback_data=f"set_language_English_{file_id}"),
                     InlineKeyboardButton("Hindi", callback_data=f"set_language_Hindi_{file_id}")]
                ])
            )

        elif action == "replace_poster":
            new_poster = await replace_poster(file_id)
            await query.message.reply_photo(photo=new_poster, caption="✅ Poster updated!")
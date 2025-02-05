#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id
import requests
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





@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    try:
        movie_query = await client.ask(
            text="Send the movie name to search in the DB Channel:",
            chat_id=message.from_user.id,
            timeout=60
        )
    except:
        return

    movie_name = movie_query.text
    search_results = await search_movie_in_db(client, movie_name)

    if not search_results:
        await message.reply("❌ No results found in the DB Channel. Try another movie name.", quote=True)
        return

    movie_data = search_results[0]  # Taking the first result (modify if needed)
    movie_title = movie_data.get('title', 'Unknown Title')
    year = movie_data.get('year', 'Unknown Year')
    language = movie_data.get('language', 'Unknown Language')
    qualities = movie_data.get('qualities', {})

    # Fetch movie poster and details
    poster_url, imdb_rating, genre, plot = await get_movie_poster(movie_title)

    links = []
    for quality, msg_ids in qualities.items():
        if isinstance(msg_ids, list) and len(msg_ids) > 1:
            # Generate batch link if multiple files exist for the same quality
            encoded_ids = [await encode(f"get-{msg_id * abs(client.db_channel.id)}") for msg_id in msg_ids]
            batch_link = f"https://t.me/{client.username}?start=batch-" + "-".join(encoded_ids)
            links.append(f"<b>{quality} (Batch):</b> <a href='{batch_link}'>Download All</a>")
        else:
            # Generate a single link if only one file exists
            msg_id = msg_ids[0] if isinstance(msg_ids, list) else msg_ids
            encoded = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
            single_link = f"https://t.me/{client.username}?start={encoded}"
            links.append(f"<b>{quality}:</b> <a href='{single_link}'>Download</a>")

    caption = (
        f"<b>{movie_title} ({year})</b>\n"
        f"<b>Language:</b> {language}\n"
        f"<b>IMDb Rating:</b> {imdb_rating} ⭐\n"
        f"<b>Genre:</b> {genre}\n\n"
        f"<b>Plot:</b> {plot}\n\n"
        + "\n".join(links)
    )

    try:
        if poster_url:
            response = requests.get(poster_url)
            poster = BytesIO(response.content)
            await message.reply_photo(photo=poster, caption=caption, parse_mode="html")
        else:
            await message.reply_text(caption, parse_mode="html")
    except:
        await message.reply_text("⚠️ Error sending the poster. Sending text instead.", parse_mode="html")
        await message.reply_text(caption, parse_mode="html")


async def search_movie_in_db(client, movie_name):
    """Function to search the DB channel for the movie and extract details."""
    # Implement logic to search DB Channel messages and extract relevant movie details
    # Example return structure:
    return [{
        "msg_id": 1234,
        "title": "Guardians of the Galaxy Vol. 2",
        "year": "2017",
        "language": "English",
        "qualities": {
            "480p": [1111, 2222],  # Example of batch links
            "720p": 3333,  # Example of a single file
            "1080p": [4444, 5555, 6666]  # Another batch example
        }
    }]


async def get_movie_poster(movie_name):
    """Fetches movie poster and additional details from OMDb API."""
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()

    if response.get("Response") == "True":
        return (
            response.get("Poster"),  # Poster URL
            response.get("imdbRating", "N/A"),  # IMDb Rating
            response.get("Genre", "Unknown"),  # Genre
            response.get("Plot", "No plot available.")  # Plot
        )

    return None, "N/A", "Unknown", "No plot available."
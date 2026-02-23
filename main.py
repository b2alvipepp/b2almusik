import os
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioQuality
from pytgcalls.types.stream import StreamAudio
from yt_dlp import YoutubeDL

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call = PyTgCalls(app)
queues = {}
current = {}

def get_audio(query):
    ydl_opts = {'format': 'bestaudio', 'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        if "youtube.com" in query or "youtu.be" in query:
            info = ydl.extract_info(query, download=False)
        else:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        return {
            'title': info['title'],
            'url': info['webpage_url'],
            'audio_url': info['url']
        }

async def play_next(chat_id):
    if chat_id in queues and queues[chat_id]:
        song = queues[chat_id].pop(0)
        current[chat_id] = song
        await call.play(chat_id, StreamAudio(song['audio_url'], audio_parameters=AudioQuality.HIGH))
        await app.send_message(chat_id, f"🎵 **Putar:** {song['title']}")

@app.on_message(filters.command("play"))
async def play(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ Pakai: /play [judul/link]")
    
    chat_id = message.chat.id
    query = " ".join(message.command[1:])
    msg = await message.reply("🔍 **Mencari...**")
    
    try:
        song = get_audio(query)
        if chat_id not in queues:
            queues[chat_id] = []
        
        if chat_id in current:
            queues[chat_id].append(song)
            await msg.edit(f"✅ **Antrian #{len(queues[chat_id])}:** {song['title']}")
        else:
            current[chat_id] = song
            await call.play(chat_id, StreamAudio(song['audio_url'], audio_parameters=AudioQuality.HIGH))
            await msg.edit(f"🎵 **Memutar:** {song['title']}")
    except Exception as e:
        await msg.edit(f"❌ Error: {str(e)}")

@app.on_message(filters.command("skip"))
async def skip(client, message):
    chat_id = message.chat.id
    await call.stop(chat_id)
    await play_next(chat_id)
    await message.reply("⏭️ **Skipped**")

@app.on_message(filters.command("stop"))
async def stop(client, message):
    chat_id = message.chat.id
    await call.stop(chat_id)
    queues[chat_id] = []
    current.pop(chat_id, None)
    await message.reply("⏹️ **Stopped**")

@call.on_stream_end()
async def end(client, update):
    await play_next(update.chat_id)

if __name__ == "__main__":
    app.run()

from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters
from info import *
import random

# A diverse set of negative/disappointed emojis (widely supported)
NEGATIVE_EMOJIS = ["😢", "🙁", "😞", "😟", "😔", "😥", "😭", "😩"]

async def get_fsub(bot, message):
    target_channel_id = AUTH_CHANNEL  # Your channel ID
    user_id = message.from_user.id
    try:
        # Check if the user is a member of the required channel
        await bot.get_chat_member(target_channel_id, user_id)
    except UserNotParticipant:
        # Generate the channel invite link
        channel_link = (await bot.get_chat(target_channel_id)).invite_link
        join_button = InlineKeyboardButton("🔔 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link)
        # Create a unique callback that includes the user's id
        check_button = InlineKeyboardButton("✅ ɪ ᴊᴏɪɴᴇᴅ", callback_data=f"check_fsub_{user_id}")

        keyboard = InlineKeyboardMarkup([[join_button], [check_button]])
        await bot.send_photo(
            chat_id=message.chat.id,
            photo="https://graph.org/file/2ee31dc74ff5644d22cdd-ddeb187edf9a4d6f3d.jpg",
            caption=(
                f"<b>ʜᴇʏ {message.from_user.mention()},</b>\n\n"
                "ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ, ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ʏᴇᴛ.\n"
                "ᴘʟᴇᴀsᴇ ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴀɴᴅ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ, ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ᴄᴏɴᴛɪɴᴜᴇ ᴜsɪɴɢ ᴍᴇ 😊\n\n"
            ),
            reply_markup=keyboard,
        )

        # React to the user's message with a random disappointed emoji
        emoji = random.choice(NEGATIVE_EMOJIS)
        await message.react(emoji)

        return False
    else:
        return True

# Callback handler to recheck membership when "I Joined" is clicked
@Client.on_callback_query(filters.regex(r"^check_fsub_(\d+)$"))
async def check_fsub_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    target_user_id = int(callback_query.data.split("_")[2])
    
    # Only allow the intended user to trigger this callback
    if user_id != target_user_id:
        await callback_query.answer("ᴛʜɪs ᴍᴇssᴀɢᴇ ɪsɴ'ᴛ ᴍᴇᴀɴᴛ ғᴏʀ ʏᴏᴜ!", show_alert=True)
        return

    try:
        await client.get_chat_member(AUTH_CHANNEL, user_id)
        await callback_query.answer("ᴛʜᴀɴᴋs ғᴏʀ ᴊᴏɪɴɪɴɢ... ʜᴇʜᴇ", show_alert=True)
        await callback_query.message.delete()
        await client.send_message(chat_id=user_id, text="ᴡᴇʟʟ, ɴᴏᴡ sᴇɴᴅ /start ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ")
    except UserNotParticipant:
        second_image = "https://graph.org/file/7a0dcc38e2e4a142e0e6e-9bce8dfc12866eb8b2.jpg"
        channel_link = (await client.get_chat(AUTH_CHANNEL)).invite_link
        join_button = InlineKeyboardButton("🔔 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=channel_link)
        check_button = InlineKeyboardButton("✅ ɪ ᴊᴏɪɴᴇᴅ", callback_data=f"check_fsub_{target_user_id}")
        keyboard = InlineKeyboardMarkup([[join_button], [check_button]])
        await callback_query.message.edit_media(
            media=InputMediaPhoto(
                media=second_image,
                caption=(
                    "sᴜᴄʜ ᴀ ʟɪᴀʀ!\n"
                    "ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ, ᴏᴛʜᴇʀᴡɪsᴇ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴄᴏɴᴛɪɴᴜᴇ"
                ),
            ),
            reply_markup=keyboard,
        )
        await callback_query.answer("ʜᴜʜ... ʏᴏᴜ ᴛʜɪɴᴋ ʏᴏᴜ ᴄᴀɴ ғᴏᴏʟ ᴍᴇ?", show_alert=True)

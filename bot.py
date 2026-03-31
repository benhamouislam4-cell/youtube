import telebot
from yt_dlp import YoutubeDL
import os

# 1. ضع التوكن الخاص بك هنا
BOT_TOKEN = '8353705136:AAEpS7o1pPzO2BL7CfT5at63WZ7wYDe0Yyc'
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "أرسل رابط يوتيوب، وسأختار لك أفضل جودة تناسب حجم الملف! 🎬")

@bot.message_handler(func=lambda message: True)
def handle_video(message):
    url = message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        return bot.reply_to(message, "يرجى إرسال رابط يوتيوب صحيح.")

    sent_msg = bot.reply_to(message, "⏳ جاري فحص الجودة والتحميل...")
    chat_id = message.chat.id
    output_file = f"video_{chat_id}.mp4"

    # 2. إعدادات الجودة الذكية (yt-dlp)
    ydl_opts = {
        # يختار أفضل فيديو MP4 + أفضل صوت M4A ويدمجهما، أو أفضل ملف MP4 جاهز
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_file,
        'max_filesize': 50 * 1024 * 1024, # حد 50 ميجا لضمان قبول تليجرام للملف
        'merge_output_format': 'mp4',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')

        # 3. إرسال الفيديو للمستخدم
        with open(output_file, 'rb') as v:
            bot.send_video(chat_id, v, caption=f"✅ {title}\nبأفضل جودة متاحة.")
        
        # تنظيف الجهاز وحذف الملف بعد الإرسال
        os.remove(output_file)
        bot.delete_message(chat_id, sent_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: الحجم قد يكون أكبر من 50MB أو الرابط غير مدعوم.", chat_id, sent_msg.message_id)
        if os.path.exists(output_file): os.remove(output_file)

bot.polling()

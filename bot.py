import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# إعداد السجلات (Logging) لمعرفة الأخطاء إن وجدت
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# دالة إعدادات التحميل (yt-dlp)
def get_ydl_opts(format_type, url):
    folder = 'downloads'
    if not os.path.exists(folder):
        os.makedirs(folder)

    # الإعدادات العامة (الكوكيز وفك التشفير)
    opts = {
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'cachedir': False,
    }

    # إضافة ملف الكوكيز إذا كان موجوداً (للستوريات وإنستغرام)
    if os.path.exists('cookies.txt'):
        opts['cookiefile'] = 'cookies.txt'

    # إعدادات الصيغة (صوت أو فيديو)
    if format_type == 'mp3':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # تحميل أفضل جودة فيديو وصوت مدمجين بصيغة MP4
        opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })
    
    return opts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت التحميل الشامل!\n\n"
        "🚀 أرسل رابطاً من (YouTube, Instagram, TikTok)\n"
        "📌 ملاحظة: اليوتيوب سيعطيك خيارات للصيغة."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # التحقق إذا كان الرابط يوتيوب لإظهار خيارات الصيغة
    if "youtube.com" in url or "youtu.be" in url:
        keyboard = [
            [
                InlineKeyboardButton("🎬 فيديو MP4", callback_data=f"mp4|{url}"),
                InlineKeyboardButton("🎵 صوت MP3", callback_data=f"mp3|{url}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اختر الصيغة المطلوبة لفيديو اليوتيوب:", reply_markup=reply_markup)
    else:
        # للإنستغرام (ريلز/ستوري) وتيك توك يتم التحميل مباشرة كفيديو
        await download_and_send(update, context, url, 'mp4')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_type, url = query.data.split('|')
    # تحديث الرسالة لإعلام المستخدم بالبدء
    await query.edit_message_text(text="⏳ جاري التحميل والمعالجة... قد يستغرق ذلك دقيقة.")
    await download_and_send(query, context, url, format_type, is_query=True)

async def download_and_send(event, context, url, format_type, is_query=False):
    # تحديد مكان إرسال الرد (رسالة عادية أم Query)
    chat_id = event.message.chat_id if not is_query else event.callback_query.message.chat_id
    temp_msg = await context.bot.send_message(chat_id=chat_id, text="🚀 بدأت عملية السحب من السيرفر...")

    ydl_opts = get_ydl_opts(format_type, url)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تصحيح الامتداد في حالة MP3
            if format_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
        # إرسال الملف للمستخدم
        with open(filename, 'rb') as file:
            if format_type == 'mp3':
                await context.bot.send_audio(chat_id=chat_id, audio=file, caption="✅ تم تحميل الصوت بنجاح")
            else:
                await context.bot.send_video(chat_id=chat_id, video=file, caption="✅ تم تحميل الفيديو بنجاح")
        
        # تنظيف: حذف الملف من الكمبيوتر بعد الإرسال
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ عذراً، حدث خطأ أثناء التحميل.\nالتفاصيل: {str(e)}")
    finally:
        await temp_msg.delete()

# تشغيل البوت
if __name__ == '__main__':
    # استبدل التوكن هنا
    TOKEN = "8265386846:AAGqz_oBtnEEBT3dPcYQJXVOiLviD4olgVc"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("--- البوت يعمل الآن بنجاح ---")
    application.run_polling()
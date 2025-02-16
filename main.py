import logging
import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 📌 ดึง TOKEN จาก Environment Variables (ปลอดภัยกว่าใส่ตรง ๆ)
TOKEN = os.getenv("TOKEN")

# 📌 ใส่ Telegram ID ของแอดมิน (รองรับหลายคน)
ADMIN_IDS = [123456789, 987654321, 1801684820]

# 📌 ตั้งค่าระบบบันทึก Log (ใช้ดูการทำงานของบอท)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 📌 ไฟล์เก็บข้อมูลลูกค้า (เพื่อให้ข้อมูลยังอยู่หลังจากบอทรีสตาร์ท)
CUSTOMER_DATA_FILE = "customer_data.json"

# 📌 โหลดข้อมูลลูกค้าจากไฟล์ (ถ้ามี)
def load_customer_data():
    if os.path.exists(CUSTOMER_DATA_FILE):
        with open(CUSTOMER_DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# 📌 บันทึกข้อมูลลูกค้าลงไฟล์
def save_customer_data():
    with open(CUSTOMER_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(customer_data, file, ensure_ascii=False, indent=4)

# 📌 โหลดข้อมูลเริ่มต้น
customer_data = load_customer_data()

# 👉 ฟังก์ชันรับข้อความจากลูกค้า และส่งให้แอดมิน
async def forward_to_admin(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    user_message = update.message.text
    user_id = user.id

    # บันทึกข้อมูลลูกค้า
    customer_data[user_id] = user.first_name
    save_customer_data()

    # ส่งข้อความจากลูกค้าไปหาแอดมิน
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📩 ข้อความจาก {user.first_name} (ID: {user_id}):\n{user_message}"
            )
        except Exception as e:
            logger.error(f"❌ ไม่สามารถส่งข้อความถึงแอดมิน {admin_id}: {e}")

# 👉 ฟังก์ชันให้แอดมินตอบกลับลูกค้าโดยใช้ /reply [ID] [ข้อความ]
async def reply_to_customer(update: Update, context: CallbackContext) -> None:
    admin_id = update.message.from_user.id
    args = update.message.text.split(" ", 2)  # แยกข้อความเป็น 3 ส่วน: คำสั่ง /reply, ID, ข้อความ

    if admin_id in ADMIN_IDS:
        if len(args) < 3:
            await update.message.reply_text("❌ ใช้คำสั่งให้ถูกต้อง: /reply [ID ลูกค้า] [ข้อความ]")
            return
        
        try:
            customer_id = int(args[1])  # ดึง ID ลูกค้าจากข้อความ
        except ValueError:
            await update.message.reply_text("❌ ID ลูกค้าต้องเป็นตัวเลข!")
            return

        message_to_send = args[2]  # ดึงข้อความที่ต้องการส่ง

        if customer_id in customer_data:
            customer_name = customer_data[customer_id]
            try:
                await context.bot.send_message(
                    chat_id=customer_id,
                    text=f"💬 แอดมิน: {message_to_send}"
                )
                await update.message.reply_text(f"✅ ส่งข้อความไปหาลูกค้า '{customer_name}' (ID: {customer_id}) แล้ว!")
            except Exception as e:
                await update.message.reply_text("❌ ไม่สามารถส่งข้อความถึงลูกค้า!")
                logger.error(f"❌ ส่งข้อความไปยัง {customer_id} ไม่สำเร็จ: {e}")
        else:
            await update.message.reply_text("❌ ไม่พบลูกค้าคนนี้!")

# 👉 ฟังก์ชัน /start สำหรับแสดงข้อความต้อนรับ
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("สวัสดี! ฉันคือบอท คุณสามารถส่งข้อความหาแอดมินได้ที่นี่ ✨")

# 👉 ฟังก์ชันหลัก
def main():
    if not TOKEN:
        logger.error("❌ TOKEN ไม่ถูกต้อง! โปรดตั้งค่า Environment Variable 'TOKEN'")
        return
    
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_customer))  # ให้แอดมินใช้ /reply
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin))  # รับข้อความจากลูกค้า

    logger.info("✅ บอทกำลังทำงาน...")
    app.run_polling()

if __name__ == "__main__":
    main()

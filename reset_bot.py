# reset_bot.py - Chạy 1 lần để reset bot
import asyncio
from telegram import Bot, BotCommand
from telegram.constants import ParseMode

BOT_TOKEN = "8862072402:AAG2T5KXVsaqSQPsQ25sj-HkClBExDVz7Jk"

async def reset():
    bot = Bot(BOT_TOKEN)
    
    # 1. Xoá tên bot
    await bot.set_my_name("LE HOANG MINH")
    print("✅ Set name: LE HOANG MINH")
    
    # 2. Xoá mô tả ngắn (hiển thị khi chưa start)
    await bot.set_my_short_description(
        "🎯 LHM TOOL - Dự đoán TÀI/XỈU chuẩn xác\n"
        "⚡ 12-Engine Deterministic AI\n"
        "📥 Gửi MD5 / SHA-256 để dự đoán"
    )
    print("✅ Set short description")
    
    # 3. Xoá mô tả dài (hiển thị khi /start lần đầu)
    await bot.set_my_description(
        "🎯 LE HOANG MINH TOOL - Dự đoán TÀI/XỈU\n\n"
        "⚡ 12-Engine Deterministic AI\n"
        "🔒 Cùng hash → cùng kết quả\n"
        "📥 Gửi MD5 (32 ký tự) hoặc SHA-256 (64 ký tự)\n\n"
        "🔑 Cần key VIP để sử dụng\n"
        "📞 Liên hệ admin: 0372834763"
    )
    print("✅ Set description")
    
    # 4. Xoá ảnh profile cũ (nếu có)
    try:
        await bot.delete_my_profile_photo()
        print("✅ Deleted profile photo")
    except Exception as e:
        print(f"⚠️ No photo to delete: {e}")
    
    # 5. Xoá TẤT CẢ commands cũ trước
    await bot.set_my_commands([])
    print("✅ Cleared old commands")
    
    # 6. Set commands mới sạch
    await bot.set_my_commands([
        BotCommand("start", "Bắt đầu"),
        BotCommand("key", "Kích hoạt key"),
        BotCommand("nap", "Nạp tiền mua key"),
        BotCommand("info", "Thông tin VIP"),
        BotCommand("thongke", "Thống kê của bạn"),
        BotCommand("32kitu", "Hướng dẫn MD5"),
        BotCommand("64kitu", "Hướng dẫn SHA-256"),
        BotCommand("hotro", "Liên hệ admin"),
        BotCommand("xoa", "Xoá tin nhắn bot"),
        BotCommand("myid", "Xem ID Telegram"),
    ])
    print("✅ Set new commands (user)")
    
    # 7. Xoá commands admin cũ (nếu có set riêng)
    await bot.delete_my_commands()
    print("✅ Final cleanup")
    
    # 8. Xoá webhook cũ
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Deleted webhook")
    
    # 9. Set menu button mặc định
    try:
        from telegram import MenuButtonCommands
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        print("✅ Set menu button = Commands")
    except Exception as e:
        print(f"⚠️ Menu button: {e}")
    
    print("\n🎉 RESET HOÀN TẤT!")
    print("→ Giờ mở Telegram, chat với bot, gõ /start để xem kết quả mới")

if __name__ == "__main__":
    asyncio.run(reset())

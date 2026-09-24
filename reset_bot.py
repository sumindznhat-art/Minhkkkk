# reset_bot.py - Chạy 1 lần để clean toàn bộ metadata
import asyncio
from telegram import Bot, BotCommand, MenuButtonCommands
from telegram.constants import ParseMode

BOT_TOKEN = "8862072402:AAG2T5KXVsaqSQPsQ25sj-HkClBExDVz7Jk"
ADMIN_ID = 8852639183

async def reset():
    bot = Bot(BOT_TOKEN)
    
    print("=" * 50)
    print("🧹 RESET BOT HOÀN TOÀN")
    print("=" * 50)
    
    # 1. Set tên bot
    try:
        await bot.set_my_name("LE HOANG MINH TOOL")
        print("✅ Set name")
    except Exception as e:
        print(f"⚠️ Name: {e}")
    
    # 2. Set mô tả ngắn (KHÔNG LINK)
    try:
        await bot.set_my_short_description(
            "🎯 LE HOANG MINH TOOL\n"
            "⚡ 12-Engine Deterministic AI\n"
            "📥 Gửi MD5 / SHA-256 để dự đoán"
        )
        print("✅ Set short description")
    except Exception as e:
        print(f"⚠️ Short desc: {e}")
    
    # 3. Set mô tả dài (KHÔNG LINK)
    try:
        await bot.set_my_description(
            "🎯 LE HOANG MINH TOOL - Dự đoán TÀI/XỈU\n\n"
            "⚡ 12-Engine Deterministic AI\n"
            "🔒 Cùng hash → cùng kết quả\n"
            "📥 Gửi MD5 (32 ký tự) hoặc SHA-256 (64 ký tự)\n\n"
            "🔑 Cần key VIP để sử dụng\n"
            "📞 Liên hệ admin: 0372834763"
        )
        print("✅ Set description")
    except Exception as e:
        print(f"⚠️ Desc: {e}")
    
    # 4. Xoá ảnh profile cũ (nếu có)
    try:
        await bot.delete_my_profile_photo()
        print("✅ Deleted profile photo")
    except Exception as e:
        print(f"⚠️ Photo: {e}")
    
    # 5. Xoá TẤT CẢ commands cũ (mọi scope)
    try:
        await bot.delete_my_commands()
        print("✅ Cleared commands (default)")
    except Exception as e:
        print(f"⚠️ {e}")
    
    # 6. Set commands user mới (10 lệnh sạch)
    user_cmds = [
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
    ]
    await bot.set_my_commands(user_cmds)
    print("✅ Set USER commands (10)")
    
    # 7. Set commands admin (đầy đủ)
    admin_cmds = user_cmds + [
        BotCommand("admin", "Admin Panel"),
        BotCommand("capkey", "Cấp key mới"),
        BotCommand("keys", "Quản lý key"),
        BotCommand("delkey", "Xoá key"),
        BotCommand("users", "Danh sách user"),
        BotCommand("giahan", "Gia hạn user"),
        BotCommand("resetkey", "Reset user"),
        BotCommand("ban", "Ban user"),
        BotCommand("unban", "Unban user"),
        BotCommand("bans", "Danh sách ban"),
        BotCommand("thongkeuser", "Thống kê user"),
        BotCommand("broadcast", "Gửi thông báo"),
        BotCommand("clearcache", "Xoá cache"),
    ]
    from telegram import BotCommandScopeChat
    try:
        await bot.set_my_commands(
            admin_cmds,
            scope=BotCommandScopeChat(chat_id=ADMIN_ID)
        )
        print(f"✅ Set ADMIN commands (chat {ADMIN_ID})")
    except Exception as e:
        print(f"⚠️ Admin cmds: {e}")
    
    # 8. Xoá webhook
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Deleted webhook")
    
    # 9. Set menu button = Commands
    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        print("✅ Set menu button")
    except Exception as e:
        print(f"⚠️ Menu: {e}")
    
    # 10. Xoá pinned message ở private chat (nếu có)
    try:
        await bot.unpin_all_chat_messages(chat_id=ADMIN_ID)
        print("✅ Unpin admin chat")
    except Exception as e:
        print(f"⚠️ Unpin: {e}")
    
    print("=" * 50)
    print("🎉 RESET HOÀN TẤT!")
    print("=" * 50)
    print("\n→ Mở Telegram, gõ /start cho bot để xem menu mới")
    print("→ Admin gõ /admin để thấy menu admin")

if __name__ == "__main__":
    asyncio.run(reset())

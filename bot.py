# ============================================================
#   🚀 POST INIT - CLEAN + ADMIN MENU
# ============================================================
async def post_init(app):
    # Xoá webhook
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Delete webhook OK")
    except Exception as e:
        logger.warning("delete_webhook: " + str(e))

    # Set tên bot
    try:
        await app.bot.set_my_name(BRAND_NAME + " TOOL")
        logger.info("Set bot name OK")
    except Exception as e:
        logger.warning("set_my_name: " + str(e))

    # Set mô tả ngắn (KHÔNG CÓ LINK)
    try:
        await app.bot.set_my_short_description(
            "🎯 " + BRAND_NAME + " TOOL\n"
            "⚡ 12-Engine Deterministic AI\n"
            "📥 Gửi MD5 / SHA-256 để dự đoán"
        )
    except Exception as e:
        logger.warning("short_desc: " + str(e))

    # Set mô tả dài (KHÔNG CÓ LINK NHÓM)
    try:
        await app.bot.set_my_description(
            "🎯 " + BRAND_NAME + " TOOL - Dự đoán TÀI/XỈU\n\n"
            "⚡ 12-Engine Deterministic AI\n"
            "🔒 Cùng hash → cùng kết quả\n"
            "📥 Gửi MD5 (32 ký tự) hoặc SHA-256 (64 ký tự)\n\n"
            "🔑 Cần key VIP để sử dụng\n"
            "📞 Liên hệ admin: " + ADMIN_PHONE
        )
    except Exception as e:
        logger.warning("desc: " + str(e))

    # XOÁ TOÀN BỘ COMMANDS CŨ (chống hijack)
    try:
        await app.bot.delete_my_commands()
        logger.info("Cleared old commands")
    except Exception as e:
        logger.warning("delete_my_commands: " + str(e))

    # XOÁ COMMANDS Ở CÁC SCOPE KHÁC (chống hijack triệt để)
    try:
        await app.bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    except Exception:
        pass
    try:
        await app.bot.delete_my_commands(scope=BotCommandScopeAllGroupChats())
    except Exception:
        pass
    try:
        await app.bot.delete_my_commands(scope=BotCommandScopeAllChatAdministrators())
    except Exception:
        pass

    # ================================================
    #   SET COMMANDS CHO USER THƯỜNG (10 lệnh)
    # ================================================
    user_commands = [
        BotCommand("start",    "🏠 Bắt đầu"),
        BotCommand("key",      "🔑 Kích hoạt key"),
        BotCommand("nap",      "💳 Nạp tiền mua key"),
        BotCommand("info",     "👤 Thông tin VIP"),
        BotCommand("thongke",  "📊 Thống kê của bạn"),
        BotCommand("32kitu",   "📘 Hướng dẫn MD5"),
        BotCommand("64kitu",   "📗 Hướng dẫn SHA-256"),
        BotCommand("hotro",    "📞 Liên hệ admin"),
        BotCommand("xoa",      "🧹 Xoá tin nhắn bot"),
        BotCommand("myid",     "🆔 Xem ID Telegram"),
    ]

    try:
        await app.bot.set_my_commands(
            user_commands,
            scope=BotCommandScopeDefault()
        )
        logger.info("Set USER commands OK (10 lenh)")
    except Exception as e:
        logger.error("set user commands: " + str(e))

    # ================================================
    #   SET COMMANDS CHO ADMIN (đầy đủ + capkey)
    # ================================================
    admin_commands = [
        BotCommand("start",        "🏠 Bắt đầu"),
        BotCommand("key",          "🔑 Kích hoạt key"),
        BotCommand("nap",          "💳 Nạp tiền mua key"),
        BotCommand("info",         "👤 Thông tin VIP"),
        BotCommand("thongke",      "📊 Thống kê của bạn"),
        BotCommand("32kitu",       "📘 Hướng dẫn MD5"),
        BotCommand("64kitu",       "📗 Hướng dẫn SHA-256"),
        BotCommand("hotro",        "📞 Liên hệ admin"),
        BotCommand("xoa",          "🧹 Xoá tin nhắn bot"),
        BotCommand("myid",         "🆔 Xem ID Telegram"),
        BotCommand("admin",        "👑 Admin Panel"),
        BotCommand("capkey",       "🔐 Cấp key mới"),
        BotCommand("keys",         "📋 Quản lý key"),
        BotCommand("delkey",       "🗑️ Xoá key"),
        BotCommand("users",        "👥 Danh sách user"),
        BotCommand("giahan",       "⏰ Gia hạn user"),
        BotCommand("resetkey",     "🔄 Reset user"),
        BotCommand("ban",          "🚫 Ban user"),
        BotCommand("unban",        "✅ Unban user"),
        BotCommand("bans",         "📛 Danh sách ban"),
        BotCommand("thongkeuser",  "📈 Thống kê user"),
        BotCommand("broadcast",    "📢 Gửi thông báo"),
        BotCommand("clearcache",   "🧹 Xoá cache"),
    ]

    for admin_id in ADMIN_IDS:
        try:
            await app.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
            logger.info("Set ADMIN commands OK (chat " + str(admin_id) + ")")
        except Exception as e:
            logger.warning("set admin commands for " + str(admin_id) + ": " + str(e))

    # Set menu button = Commands
    try:
        await app.bot.set_chat_menu_button(
            menu_button=MenuButtonCommands()
        )
        logger.info("Set menu button OK")
    except Exception as e:
        logger.warning("set_chat_menu_button: " + str(e))

    logger.info("DATA_DIR: " + DATA_DIR)
    logger.info(BRAND_NAME + " TOOL v16 CLEAN started!")

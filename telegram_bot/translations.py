"""
Translation strings for Lynk Telegram Bot in English, Russian, and Uzbek.
"""

TRANSLATIONS = {
    'en': {
        # Bot Core & Commands
        'welcome_linked': (
            "🎉 *Success!* Your account *{username}* has been successfully linked to Lynk.\n\n"
            "You will now receive notifications here for sales, new messages, and status updates."
        ),
        'welcome_unlinked': (
            "👋 *Welcome to Lynk Bot!*\n\n"
            "I can notify you when you get new orders (sales), chat messages, and KYC status updates.\n\n"
            "To link your account, you can:\n"
            "1. Log in on the website, go to your profile, and click *Link Telegram Bot*.\n"
            "2. Or, log in directly here using the command:\n"
            "   `/login <username_or_email> <password>`\n\n"
            "🌐 *Language:* Use `/language` to change your preferred language."
        ),
        'invalid_token': (
            "❌ *Invalid Link Code.*\n"
            "Please generate a new linking code from your profile settings on the website."
        ),
        'login_usage': (
            "⚠️ *Usage:*\n"
            "`/login <username_or_email_or_phone> <password>`\n\n"
            "Example:\n"
            "`/login daler mysecurepassword`"
        ),
        'user_not_found': "❌ *Error:* No user found with that identifier.",
        'login_success': (
            "🎉 *Success!* Logged in successfully as *{username}*.\n\n"
            "Your Telegram is now linked to Lynk."
        ),
        'login_invalid_password': "❌ *Error:* Invalid password.",
        'account_pending_deletion': "❌ *Error:* This account is pending deletion.",
        'logout_success': "🔌 *Logged out.* Account *{username}* has been unlinked from this Telegram.",
        'logout_not_logged_in': "ℹ️ You are not logged in or linked to any Lynk account.",
        'status_linked': (
            "ℹ️ *Status: Linked*\n"
            "• *Username:* {username}\n"
            "• *Role:* {role}\n"
            "• *Language:* {language_name}\n"
            "• *Notifications:* {notifications}"
        ),
        'status_unlinked': "ℹ️ *Status: Unlinked*\n\nTo link your account, use `/login` or link from the website.\n• *Language:* {language_name}",
        'language_prompt': (
            "🌐 *Select your preferred language / Выберите язык / Tilni tanlang:*"
        ),
        'language_changed': "✅ *Language updated to English.* 🇬🇧",
        'help_text': (
            "💡 *Available Commands:*\n\n"
            "• `/login <username> <password>` - Log in and link your Lynk account\n"
            "• `/logout` - Unlink your account\n"
            "• `/status` - Check your link status and settings\n"
            "• `/language` - Change language (English / Русский / Oʻzbekcha)\n"
            "• `/help` - Show this help message"
        ),
        'unknown_command': (
            "❓ *Unknown Command.*\n"
            "Type `/help` to see the list of available commands."
        ),
        'enabled': "Enabled",
        'disabled': "Disabled",

        # Event Notifications
        'notif_new_sale': (
            "🔔 *New Sale!*\n"
            "Order #`{order_id}` has been placed by *{buyer}*.\n"
            "💰 *Total Price:* {total_price} {currency}\n"
            "📊 *Status:* {status}"
        ),
        'notif_order_status_updated': (
            "📦 *Order Status Updated*\n"
            "Order #`{order_id}` has been updated to *{status}*."
        ),
        'notif_new_chat_message': (
            "💬 *New Message from {sender}*\n\n"
            "{message}"
        ),
        'notif_seller_verified': (
            "✅ *Seller Profile Verified!*\n"
            "Your seller account for *{company_name}* has been verified by the administration. "
            "You can now list products and start selling!"
        ),
        'notif_kyc_updated': (
            "👤 *KYC Verification Update*\n"
            "Your KYC Selfie verification status has been updated to: *{status}*.\n"
            "📝 *Notes:* {notes}"
        ),
        'notif_report_submitted': (
            "⚠️ *New Report Submitted*\n"
            "• *Reporter:* {reporter}\n"
            "• *Type:* {type}\n"
            "• *Reason:* {reason}\n"
            "• *Description:* {description}"
        ),
    },

    'ru': {
        # Bot Core & Commands
        'welcome_linked': (
            "🎉 *Успешно!* Ваш аккаунт *{username}* привязан к Lynk.\n\n"
            "Теперь вы будете получать уведомления о продажах, новых сообщениях и обновлениях статуса."
        ),
        'welcome_unlinked': (
            "👋 *Добро пожаловать в бота Lynk!*\n\n"
            "Я могу уведомлять вас о новых заказах (продажах), чат-сообщениях и статусе верификации KYC.\n\n"
            "Чтобы привязать аккаунт, вы можете:\n"
            "1. Войти на сайт, перейти в настройки профиля и нажать *Привязать Telegram Bot*.\n"
            "2. Или войти прямо здесь командой:\n"
            "   `/login <логин_или_email> <пароль>`\n\n"
            "🌐 *Язык:* Используйте `/language` для смены языка."
        ),
        'invalid_token': (
            "❌ *Недействительный код привязки.*\n"
            "Пожалуйста, сгенерируйте новый код привязки в настройках профиля на сайте."
        ),
        'login_usage': (
            "⚠️ *Использование:*\n"
            "`/login <логин_email_или_телефон> <пароль>`\n\n"
            "Пример:\n"
            "`/login daler mysecurepassword`"
        ),
        'user_not_found': "❌ *Ошибка:* Пользователь с таким логином/email/телефоном не найден.",
        'login_success': (
            "🎉 *Успешно!* Вы вошли как *{username}*.\n\n"
            "Ваш Telegram аккаунт привязан к Lynk."
        ),
        'login_invalid_password': "❌ *Ошибка:* Неверный пароль.",
        'account_pending_deletion': "❌ *Ошибка:* Этот аккаунт ожидает удаления.",
        'logout_success': "🔌 *Выход выполнен.* Аккаунт *{username}* отвязан от этого Telegram.",
        'logout_not_logged_in': "ℹ️ Вы не вошли в аккаунт и не привязаны к Lynk.",
        'status_linked': (
            "ℹ️ *Статус: Привязан*\n"
            "• *Имя пользователя:* {username}\n"
            "• *Роль:* {role}\n"
            "• *Язык:* {language_name}\n"
            "• *Уведомления:* {notifications}"
        ),
        'status_unlinked': "ℹ️ *Статус: Не привязан*\n\nЧтобы привязать аккаунт, используйте `/login` или привяжите на сайте.\n• *Язык:* {language_name}",
        'language_prompt': (
            "🌐 *Select your preferred language / Выберите язык / Tilni tanlang:*"
        ),
        'language_changed': "✅ *Язык изменен на Русский.* 🇷🇺",
        'help_text': (
            "💡 *Доступные команды:*\n\n"
            "• `/login <логин> <пароль>` - Войти и привязать аккаунт Lynk\n"
            "• `/logout` - Отвязать аккаунт\n"
            "• `/status` - Проверить статус привязки и настройки\n"
            "• `/language` - Изменить язык (English / Русский / Oʻzbekcha)\n"
            "• `/help` - Показать это справочное сообщение"
        ),
        'unknown_command': (
            "❓ *Неизвестная команда.*\n"
            "Введите `/help`, чтобы увидеть список доступных команд."
        ),
        'enabled': "Включено",
        'disabled': "Отключено",

        # Event Notifications
        'notif_new_sale': (
            "🔔 *Новая продажа!*\n"
            "Заказ #`{order_id}` оформлен покупателем *{buyer}*.\n"
            "💰 *Сумма:* {total_price} {currency}\n"
            "📊 *Статус:* {status}"
        ),
        'notif_order_status_updated': (
            "📦 *Статус заказа обновлен*\n"
            "Статус заказа #`{order_id}` изменен на *{status}*."
        ),
        'notif_new_chat_message': (
            "💬 *Новое сообщение от {sender}*\n\n"
            "{message}"
        ),
        'notif_seller_verified': (
            "✅ *Профиль продавца подтвержден!*\n"
            "Ваш аккаунт продавца для *{company_name}* успешно верифицирован администрацией. "
            "Теперь вы можете добавлять товары и продавать!"
        ),
        'notif_kyc_updated': (
            "👤 *Обновление верификации KYC*\n"
            "Статус верификации вашего KYC селфи обновлен: *{status}*.\n"
            "📝 *Заметки:* {notes}"
        ),
        'notif_report_submitted': (
            "⚠️ *Поступила новая жалоба*\n"
            "• *Отправитель:* {reporter}\n"
            "• *Тип:* {type}\n"
            "• *Причина:* {reason}\n"
            "• *Описание:* {description}"
        ),
    },

    'uz': {
        # Bot Core & Commands
        'welcome_linked': (
            "🎉 *Muvaffaqiyatli!* Sizning *{username}* hisobingiz Lynk'ga ulandi.\n\n"
            "Endi bu yerda sotuvlar, yangi xabarlar va status yangilanishlari haqida bildirishnomalar olasiz."
        ),
        'welcome_unlinked': (
            "👋 *Lynk Botiga xush kelibsiz!*\n\n"
            "Men sizga yangi buyurtmalar (sotuvlar), chat xabarlari va KYC tasdiqlash statusi haqida xabar bera olaman.\n\n"
            "Hisobingizni ulash uchun:\n"
            "1. Saytga kiring, profil sozlamalariga o'ting va *Telegram Botni ulash* tugmasini bosing.\n"
            "2. Yoki to'g'ridan-to'g'ri shu yerda quyidagi buyruq orqali kiring:\n"
            "   `/login <foydalanuvchi_nomi_yoki_email> <parol>`\n\n"
            "🌐 *Til:* Tilni o'zgartirish uchun `/language` buyrug'idan foydalaning."
        ),
        'invalid_token': (
            "❌ *Yaroqsiz ulash kodi.*\n"
            "Iltimos, saytdagi profil sozlamalaridan yangi ulash kodini yarating."
        ),
        'login_usage': (
            "⚠️ *Foydalanish:*\n"
            "`/login <foydalanuvchi_nomi_email_yoki_telefon> <parol>`\n\n"
            "Misol:\n"
            "`/login daler mysecurepassword`"
        ),
        'user_not_found': "❌ *Xatolik:* Ushbu ma'lumotga ega foydalanuvchi topilmadi.",
        'login_success': (
            "🎉 *Muvaffaqiyatli!* *{username}* sifatida tizimga kirdingiz.\n\n"
            "Sizning Telegram hisobingiz Lynk'ga ulandi."
        ),
        'login_invalid_password': "❌ *Xatolik:* Parol noto'g'ri.",
        'account_pending_deletion': "❌ *Xatolik:* Ushbu hisob o'chirilish kutilmoqda.",
        'logout_success': "🔌 *Tizimdan chiqildi.* *{username}* hisobi ushbu Telegram'dan uzildi.",
        'logout_not_logged_in': "ℹ️ Siz tizimga kirmagansiz yoki biron bir Lynk hisobiga ulanmagansiz.",
        'status_linked': (
            "ℹ️ *Status: Ulandilar*\n"
            "• *Foydalanuvchi nomi:* {username}\n"
            "• *Rol:* {role}\n"
            "• *Til:* {language_name}\n"
            "• *Bildirishnomalar:* {notifications}"
        ),
        'status_unlinked': "ℹ️ *Status: Ulanmagan*\n\nHisobni ulash uchun `/login` buyrug'idan foydalaning yoki saytdan ulaning.\n• *Til:* {language_name}",
        'language_prompt': (
            "🌐 *Select your preferred language / Выберите язык / Tilni tanlang:*"
        ),
        'language_changed': "✅ *Til Oʻzbekchaga oʻzgartirildi.* 🇺🇿",
        'help_text': (
            "💡 *Mavjud buyruqlar:*\n\n"
            "• `/login <foydalanuvchi_nomi> <parol>` - Tizimga kirish va Lynk hisobini ulash\n"
            "• `/logout` - Hisobni uzish\n"
            "• `/status` - Ulanish statusi va sozlamalarni tekshirish\n"
            "• `/language` - Tilni o'zgartirish (English / Русский / Oʻzbekcha)\n"
            "• `/help` - Ushbu yordam xabarini ko'rsatish"
        ),
        'unknown_command': (
            "❓ *Noma'lum buyruq.*\n"
            "Mavjud buyruqlar ro'yxatini ko'rish uchun `/help` deb yozing."
        ),
        'enabled': "Yoqilgan",
        'disabled': "O'chirilgan",

        # Event Notifications
        'notif_new_sale': (
            "🔔 *Yangi sotuv!*\n"
            "Buyurtma #`{order_id}` xaridor *{buyer}* tomonidan joylashtirildi.\n"
            "💰 *Umumiy narx:* {total_price} {currency}\n"
            "📊 *Status:* {status}"
        ),
        'notif_order_status_updated': (
            "📦 *Buyurtma statusi yangilandi*\n"
            "Buyurtma #`{order_id}` statusi *{status}*ga o'zgartirildi."
        ),
        'notif_new_chat_message': (
            "💬 *{sender} dan yangi xabar*\n\n"
            "{message}"
        ),
        'notif_seller_verified': (
            "✅ *Sotuvchi profili tasdiqlandi!*\n"
            "Sizning *{company_name}* uchun sotuvchi hisobingiz ma'muriyat tomonidan tasdiqlandi. "
            "Endi mahsulotlarni joylashtirishingiz va sotishingiz mumkin!"
        ),
        'notif_kyc_updated': (
            "👤 *KYC tasdiqlash yangilandi*\n"
            "Sizning KYC Selfie tasdiqlash statusim *{status}*ga yangilandi.\n"
            "📝 *Eslatmalar:* {notes}"
        ),
        'notif_report_submitted': (
            "⚠️ *Yangi shikoyat kelib tushdi*\n"
            "• *Yuboruvchi:* {reporter}\n"
            "• *Turi:* {type}\n"
            "• *Sababi:* {reason}\n"
            "• *Tavsifi:* {description}"
        ),
    }
}

LANGUAGE_NAMES = {
    'en': 'English 🇬🇧',
    'ru': 'Русский 🇷🇺',
    'uz': 'Oʻzbekcha 🇺🇿',
}

def get_text(key, lang='en', **kwargs):
    """Retrieves a translated template string formatted with kwargs."""
    if lang not in TRANSLATIONS:
        lang = 'en'
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    template = lang_dict.get(key) or TRANSLATIONS['en'].get(key, '')
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template

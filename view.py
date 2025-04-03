import os
import random as rnd
from datetime import datetime, date, timedelta
from model import AddressBook, Record, ModelError # Імпортуємо ModelError для використання ключів повідомлень

# ============================ КОЛЬОРИ ТА ФОРМАТУВАННЯ ============================

class Colors:
    """Клас для зберігання ANSI кодів кольорів та стилів тексту."""
    RED       = '\033[91m'
    GREEN     = '\033[92m'
    YELLOW    = '\033[93m'
    BLUE      = '\033[94m'
    MAGENTA   = '\033[95m'
    CYAN      = '\033[96m'
    WHITE     = '\033[97m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    END       = '\033[0m'


# ============================ СЛОВНИК ПОВІДОМЛЕНЬ ============================
# Ключі відповідають значенням ModelError Enum

MESSAGES = {
    ModelError.INVALID_CONTACT_NAME.value  : f"⛔ {Colors.RED}Некоректне ім’я: {{name}}. Дозволено літери, апостроф, дефіс, пробіл.{Colors.END}",
    ModelError.INVALID_PHONE.value         : f"⛔ {Colors.RED}Невірний формат номера: {{phone}}. Має бути 10 цифр.{Colors.END}",
    ModelError.INVALID_EMAIL.value         : f"⛔ {Colors.RED}Невірний формат email: {{email}}.{Colors.END}",
    ModelError.INVALID_BIRTHDAY.value      : f"⛔ {Colors.RED}Невірний формат дати або майбутня дата: {{birthday}}. Використовуйте DD.MM.YYYY.{Colors.END}",

    ModelError.CONTACT_NOT_FOUND.value     : f"🤔 {Colors.YELLOW}Контакт з іменем '{{name}}' не знайдено.{Colors.END}",
    ModelError.CONTACT_EXISTS.value        : f"😲 {Colors.YELLOW}Контакт з іменем '{{name}}' вже існує.{Colors.END}",
    ModelError.PHONE_NOT_FOUND.value       : f"🤔 {Colors.YELLOW}Телефон з індексом {{index}} не знайдено у контакта '{{name}}'.{Colors.END}",
    ModelError.EMAIL_NOT_FOUND.value       : f"🤔 {Colors.YELLOW}Email з індексом {{index}} не знайдено у контакта '{{name}}'.{Colors.END}",
    ModelError.DUPLICATE_PHONE.value       : f"😲 {Colors.YELLOW}Номер {{phone}} вже існує у контакта '{{name}}'.{Colors.END}",
    ModelError.DUPLICATE_EMAIL.value       : f"😲 {Colors.YELLOW}Email {{email}} вже існує у контакта '{{name}}'.{Colors.END}",
    ModelError.BIRTHDAY_NOT_SET.value      : f"ℹ️ {Colors.BLUE}День народження для контакту '{{name}}' не встановлено.{Colors.END}",
    ModelError.EMPTY_CONTACTS.value        : f"ℹ️ {Colors.BLUE}Адресна книга порожня.{Colors.END}",
    ModelError.INVALID_INDEX.value         : f"⛔ {Colors.RED}Вказано недійсний індекс: {{index}}.{Colors.END}",
    ModelError.EMPTY_CONTACT_FIELDS.value  : f"ℹ️ {Colors.BLUE}Контакт {{name}} не містить телефонів чи email.{Colors.END}",

    "invalid_command"         : f"😕 {Colors.YELLOW}Невідома команда: '{{command}}'. Введіть '?' для допомоги.{Colors.END}",
    "invalid_arguments"       : f"🤔 {Colors.YELLOW}Невірні аргументи для команди '{{command}}'. Очікується: {{expected}}{Colors.END}",
    "unknown_error"           : f"🆘 {Colors.RED}Сталася невідома помилка.{Colors.END}", # Запасний варіант

    "contact_added"           : f"✅ {Colors.GREEN}Контакт '{{name}}' додано до книги.{Colors.END}",
    "phone_added"             : f"✅ {Colors.GREEN}Номер {{phone}} додано до контакту '{{name}}'.{Colors.END}",
    "email_added"             : f"✅ {Colors.GREEN}Email {{email}} додано до контакту '{{name}}'.{Colors.END}",
    "birthday_added"          : f"✅ {Colors.GREEN}День народження {{birthday}} додано для контакту '{{name}}'.{Colors.END}",
    "phone_changed"           : f"✅ {Colors.GREEN}Номер за індексом {{index}} для '{{name}}' змінено на {{new_phone}}.{Colors.END}",
    "email_changed"           : f"✅ {Colors.GREEN}Email за індексом {{index}} для '{{name}}' змінено на {{new_email}}.{Colors.END}",
    "birthday_changed"        : f"✅ {Colors.GREEN}День народження для '{{name}}' змінено на {{new_birthday}}.{Colors.END}",
    "contact_deleted"         : f"✅ {Colors.GREEN}Контакт '{{name}}' успішно видалено.{Colors.END}",
    "phone_deleted"           : f"✅ {Colors.GREEN}Телефон за індексом {{index}} у '{{name}}' видалено.{Colors.END}",
    "email_deleted"           : f"✅ {Colors.GREEN}Email за індексом {{index}} у '{{name}}' видалено.{Colors.END}",
    "birthday_deleted"        : f"✅ {Colors.GREEN}День народження для '{{name}}' видалено.{Colors.END}",

    "goodbye_message"         : f"👋 {Colors.GREEN}До побачення!{Colors.END}",
    "command_prompt"          : f"{Colors.BOLD}Введіть команду > {Colors.END}",
    "empty_contacts"          : f"ℹ️ {Colors.BLUE}Адресна книга порожня.{Colors.END}",
    "contact_details_header"  : f"📒 {Colors.BOLD}Інформація про контакт '{{name}}':{Colors.END}",
    "no_phones"               : "  📞 Телефони: Немає",
    "contact_phones"          : "  📞 Телефони: {phones_str}",
    "no_emails"               : "  📧 Emails: Немає",
    "contact_emails"          : "  📧 Emails: {emails_str}",
    "no_birthday"             : "  🎂 День народження: Не вказано",
    "contact_birthday"        : "  🎂 День народження: {birthday_str}",
    "all_contacts_header"     : f"📖 {Colors.BOLD}Усі контакти в книзі:{Colors.END}",
    "contacts_count"          : f"📊 {Colors.BLUE}Всього контактів: {{count}}.{Colors.END}",
    "birthdays_header"        : f"🎉 {Colors.BOLD}Найближчі дні народження (наступні {{days}} днів):{Colors.END}",
    "no_upcoming_birthdays"   : f"ℹ️ {Colors.BLUE}На найближчі {{days}} днів немає днів народжень.{Colors.END}",
    "help_header"             : f"🆘 {Colors.BOLD}Список доступних команд:{Colors.END}",
}

# Повний перелік вітань користувача (як було раніше)
HELLO_OPTIONS = (
    "👋 Привіт! Чим можу допомогти? (введіть '?' для списку команд)",
    'Вітаю! Я тут, щоб допомогти.', 'Добрий день! Я до ваших послуг.',
    'Привіт, як справи?', 'Гей, як ся маєш?', 'Привіт-привіт! Що треба? 😉', 'Гей! Чекаю на твої команди.',
    'Йо! Що сьогодні робимо?', 'О, привітулі!', 'Слухаю уважно 🤖', 'Чим можу допомогти, друже?',
    'Вітаю! Як можу бути корисним?', 'Добрий день! Що вас цікавить?', 'Ласкаво прошу! Чим можу допомогти?',
    'Сервіс активовано. Що вам потрібно?', 'Біп-буп! Робобот до ваших послуг! 🤖',
    'Завантаження ввічливості... 100% – Привіт!', 'Хтось викликав штучний інтелект? 👀',
    'Привіт, людська істото! Що потрібно?', 'Хей! Давай працювати! 🚀', 'Здоровенькі були! Що треба?',
    'Поїхали! Я готовий до роботи!', 'Готовий до виклику! Що потрібно?', 'Я тут! Почнімо.',
    'Адресна книга відкрита! Що робимо?', 'Запити приймаються! Чим допомогти?',
    'Когось шукаємо? Я готовий!', 'Контакти? Команди? Що цікавить?', 'Починаємо роботу. Введіть команду.'
)


# Дні тижня для гарного виводу днів народжень
DAYS_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']

# ============================ БАЗОВІ МЕТОДИ ============================

def clear_screen():
    """Очищує екран консолі."""
    os.system('cls' if os.name == 'nt' else 'clear')

def say_hello():
    """Виводить випадкове вітання."""
    print(rnd.choice(HELLO_OPTIONS))

# ============================ МЕТОДИ ВЗАЄМОДІЇ ============================

def ask() -> str:
    """Запитує команду у користувача."""
    return input(MESSAGES["command_prompt"])

def _print_message(key: str, **kwargs):
    """Базова функція для виводу повідомлень за ключем."""
    message_template = MESSAGES.get(key, MESSAGES["unknown_error"])
    try:
        print(message_template.format(**kwargs))
    except KeyError as e:
        # Якщо в шаблоні є плейсхолдер, для якого не передали аргумент
        print(f"{Colors.RED}Помилка форматування повідомлення '{key}': відсутній аргумент {e}{Colors.END}")
        print(f"Отримані аргументи: {kwargs}")
        print(f"Шаблон: {message_template}")
def cursor_up(lines: int = 1):
    """Переміщує курсор вгору на задану кількість рядків."""
    """Використовує ANSI escape код для переміщення курсора."""
    print(f"\033[{lines}A", end='')

def info(key: str, **kwargs):
    """Виводить інформаційне повідомлення."""
    _print_message(key, **kwargs)

def success(key: str, **kwargs):
    """Виводить повідомлення про успіх."""
    _print_message(key, **kwargs)

def warn(key: str, **kwargs):
    """Виводить попередження."""
    _print_message(key, **kwargs)

def error(key: str, **kwargs):
    """Виводить повідомлення про помилку."""
    _print_message(key, **kwargs)

# ============================ СПЕЦИФІЧНІ МЕТОДИ ВІДОБРАЖЕННЯ ============================

def show_contact(record: Record):
    """Виводить детальну інформацію про один контакт."""
    info("contact_details_header", name=record.name.value)

    if record.phones:
        phones_str = "; ".join(f"{Colors.CYAN}[{i}]{Colors.END} {p.value}" for i, p in enumerate(record.phones))
        info("contact_phones", phones_str=phones_str)
    else:
        info("no_phones")

    if record.emails:
        emails_str = "; ".join(f"{Colors.CYAN}[{i}]{Colors.END} {e.value}" for i, e in enumerate(record.emails))
        info("contact_emails", emails_str=emails_str)
    else:
        info("no_emails")

    if record.birthday:
        info("contact_birthday", birthday_str=str(record.birthday))
    else:
        info("no_birthday")


def show_all_contacts(book: AddressBook):
    """Виводить всі контакти з книги."""
    if not book.data:
        warn("empty_contacts")
        return

    info("all_contacts_header")
    print("═" * 50) # Розділювач
    for record in book.data.values():
        # Використовуємо ту саму функцію для одного контакту
        show_contact(record)
        print("─" * 50) # Розділювач між контактами

    info("contacts_count", count=len(book.data))


def show_upcoming_birthdays(birthdays_list: list[dict], days: int):
    """Виводить список найближчих днів народження."""
    info("birthdays_header", days=days)
    if not birthdays_list:
        info("no_upcoming_birthdays", days=days)
        return

    print(f"{Colors.BOLD}{'Ім\'я':<20} {'Дата привітання':<18} {'День тижня':<5}{Colors.END}")
    print("═" * 50)
    for item in birthdays_list:
        name = item['name']
        congrats_date_str = item['congratulation_date']
        try:
             congrats_date = datetime.strptime(congrats_date_str, '%d.%m.%Y').date()
             day_name = DAYS_NAMES[congrats_date.weekday()]

             # Виділимо сьогоднішні та завтрашні дні народження
             today = date.today()
             delta = (congrats_date - today).days
             color = Colors.END
             if delta == 0:
                 day_name = f"{Colors.GREEN}Сьогодні!{Colors.END}"
                 color = Colors.GREEN
             elif delta == 1:
                 day_name = f"{Colors.YELLOW}Завтра{Colors.END}"
                 color = Colors.YELLOW
             elif congrats_date.weekday() == 0 and item['original_weekday'] >= 5:
                  day_name = f"{Colors.CYAN}Пн (з вих){Colors.END}" # Позначимо перенесені
                  color = Colors.CYAN

             print(f"{color}{name:<20}{Colors.END} {congrats_date_str:<18} {day_name:<5}")

        except ValueError:
             # На випадок некоректної дати у списку (не повинно бути)
             print(f"{Colors.RED}Помилка даних для {name}{Colors.END}")
    print("─" * 50)


def show_help():
    """Виводить довідку по командам."""
    info("help_header")
    # Використовуємо стиль з відступами
    commands_help = [
        ("hello",                                  "Привітання"),
        ("add <ім'я> <телефон>",                   "Додати новий контакт з телефоном"),
        ("add@ <ім'я> <email>",                    "Додати новий контакт з email (або 'add-email')"),
        ("add-phone <ім'я> <телефон>",             "Додати ще один телефон існуючому контакту"),
        ("add-email <ім'я> <email>",               "Додати ще один email існуючому контакту (або 'add@')"),
        ("change <ім'я> p.<індекс> <новий тел>",   "Змінити телефон за індексом (p=phone)"),
        ("change <ім'я> e.<індекс> <новий email>", "Змінити email за індексом (e=email)"),
        ("phone <ім'я>",                           "Показати всі дані контакту (телефони, email, д/н)"),
        ("all",                                    "Показати всі контакти в книзі"),
        ("delete <ім'я>",                          "Видалити контакт"),
        ("del-phone <ім'я> <індекс>",              "Видалити телефон за індексом"),
        ("del-email <ім'я> <індекс>",              "Видалити email за індексом"),
        ("add-birthday <ім'я> <ДД.ММ.РРРР>",       "Додати/змінити дату народження (або 'add-bd')"),
        ("show-birthday <ім'я>",                   "Показати дату народження (або 'show-bd')"),
        ("del-birthday <ім'я>",                    "Видалити дату народження (або 'del-bd')"),
        ("birthdays [дні]",                        "Показати дні народження на наступні N днів (за замовч. 7) (або 'all-bd')"),
        ("clr",                                    "Очистити екран"),
        ("?",                                      "Показати цю довідку (або 'help')"),
        ("exit",                                   "Вийти з програми (або 'close', 'quit')"),
    ]
    max_cmd_len = max(len(cmd[0]) for cmd in commands_help)
    for cmd, desc in commands_help:
        print(f"  {Colors.CYAN}{cmd:<{max_cmd_len}}{Colors.END} - {desc}")
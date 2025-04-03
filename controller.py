import view as v
import model as mdl
from functools import wraps
from model import AddressBook, Record, ModelError # Імпортуємо ModelError та класи моделі
# Імпортуємо кастомні винятки
from model import CommandException, ContactException, PhoneException, EmailException, BirthdayException


# ============================ ДЕКОРАТОР ОБРОБКИ ПОМИЛОК ============================

def input_error(func):
    """
    Декоратор для обробки кастомних винятків,
    що виникають під час виконання команди.
    """
    @wraps(func)
    def wrapper(*args, **kwargs): # kwargs тут - це аргументи wrapper, а не винятку
        try:
            return func(*args, **kwargs)
        except (CommandException, ContactException, PhoneException, EmailException, BirthdayException) as e:
            error_code_value = e.error_code.value
            # Використовуємо e.kwargs, які ми зберегли у винятку
            v.error(error_code_value, **e.kwargs)
            return False
        # Змінюємо обробку ValueError та IndexError, щоб передати більше контексту
        except ValueError as e:
            # Передаємо аргументи команди, якщо вони є, для контексту
            cmd_args = args[0] if args and isinstance(args[0], list) else []
            v.error("invalid_arguments", args=cmd_args, error_message=str(e))
            return False
        except IndexError:
            # Передаємо аргументи команди
            cmd_args = args[0] if args and isinstance(args[0], list) else []
            v.error("invalid_arguments", args=cmd_args, error_message="Недостатньо аргументів або невірний індекс")
            return False
        except KeyError as e:
            # Ймовірно, не знайшли контакт за іменем (ключем)
            v.error(ModelError.CONTACT_NOT_FOUND.value, name=str(e)) # Використовуємо ключ з Enum
            return False
        except Exception as e: # Захоплюємо будь-які інші несподівані винятки
            v.error("unknown_error", error_message=str(e))
            print(f"[Debug] Неочікувана помилка: {type(e).__name__}: {e}") # Для відладки
            return False
    return wrapper


# ============================ ПАРСИНГ ВВОДУ ============================

def parse_input(user_input: str) -> tuple[str, list[str]]:
    """
    Розбирає рядок вводу на команду та аргументи.
    Повертає команду в нижньому регістрі та список аргументів.
    """
    parts = user_input.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args


# ============================ ФУНКЦІЇ-ОБРОБНИКИ КОМАНД ============================
# Всі обробники тепер приймають book як аргумент

@input_error
def add_contact(args: list[str], book: AddressBook) -> bool:
    """
    Обробляє команду 'add'.
    Додає новий контакт з іменем та телефоном або додає телефон до існуючого.
    """
    if len(args) != 2:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'add'.")
    name, phone = args

    try:
        # Спробувати знайти існуючий контакт
        record = book.find(name)
        # Якщо знайдено, додаємо телефон (може кинути PhoneException)
        record.add_phone(phone)
        v.success("phone_added", name=name, phone=phone)
    except ContactException as e:
        if e.error_code == ModelError.CONTACT_NOT_FOUND:
            # Якщо не знайдено, створюємо новий запис
            # (може кинути ContactException, PhoneException)
            record = Record(name)
            record.add_phone(phone)
            book.add_record(record) # Може кинути ContactException
            v.success("contact_added", name=name) # Використовуємо повідомлення про створення контакту
        else:
            # Прокидаємо інші ContactException далі для обробки декоратором
            raise e

    return True # Сигналізує, що були зміни для збереження


@input_error
def add_email_to_contact(args: list[str], book: AddressBook) -> bool:
    """
    Обробляє команду 'add-email' або 'add@'.
    Додає новий контакт з іменем та email або додає email до існуючого.
    """
    if len(args) != 2:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'add-email' або 'add@'.")
    name, email = args

    try:
        record = book.find(name)
        # Якщо знайдено, додаємо email (може кинути EmailException)
        record.add_email(email)
        v.success("email_added", name=name, email=email)
    except ContactException as e:
        if e.error_code == ModelError.CONTACT_NOT_FOUND:
            # Створюємо новий контакт
            record = Record(name) # Може кинути ContactException
            record.add_email(email) # Може кинути EmailException
            book.add_record(record)
            v.success("contact_added", name=name) # Повідомлення про створення
        else:
            raise e # Прокидаємо інші ContactException

    return True


@input_error
def add_extra_phone(args: list[str], book: AddressBook) -> bool:
     """
     Обробляє команду 'add-phone'.
     Додає додатковий телефон до ІСНУЮЧОГО контакту.
     """
     if len(args) != 2:
         raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'add-phone'.")
     name, phone = args
     record = book.find(name) # Кине ContactException, якщо не знайдено
     record.add_phone(phone)   # Кине PhoneException
     v.success("phone_added", name=name, phone=phone)
     return True


@input_error
def add_extra_email(args: list[str], book: AddressBook) -> bool:
     """
     Обробляє команду 'add-email'.
     Додає додатковий email до ІСНУЮЧОГО контакту.
     (Використовуємо спільний обробник для add@ i add-email для цього випадку)
     """
     if len(args) != 2:
          raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'add-email' або 'add@'.")
     name, email = args
     record = book.find(name) # Кине ContactException
     record.add_email(email)   # Кине EmailException
     v.success("email_added", name=name, email=email)
     return True


@input_error
def change_contact_field(args: list[str], book: AddressBook) -> bool:
    """
    Обробляє команду 'change'.
    Змінює телефон або email за індексом ('p.' або 'e.').
    """
    if len(args) != 3:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'change'. Очікується: <ім'я> <p|e>.<індекс> <нове значення>")
    name, index_field, new_value = args

    record = book.find(name) # Кине ContactException

    try:
        field_type, index_str = index_field.split('.')
        index = int(index_str)
    except (ValueError, IndexError):
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірний формат індексу поля у команді 'change'. Використовуйте 'p.індекс' або 'e.індекс'.")

    if field_type.lower() == 'p':
        # Змінюємо телефон (може кинути PhoneException)
        record.edit_phone(index, new_value)
        v.success("phone_changed", name=name, index=index, new_phone=new_value)
    elif field_type.lower() == 'e':
        # Змінюємо email (може кинути EmailException)
        record.edit_email(index, new_value)
        v.success("email_changed", name=name, index=index, new_email=new_value)
    else:
         # Неправильний тип поля (p або e)
         raise CommandException(ModelError.INVALID_COMMAND, message="Невірний тип поля для зміни. Використовуйте 'p' для телефону або 'e' для email.")

    return True


@input_error
def delete_contact(args: list[str], book: AddressBook) -> bool:
    """Обробляє команду 'delete'. Видаляє контакт за іменем."""
    if len(args) != 1:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'delete'.")
    name = args[0]
    book.delete(name) # Кине ContactException, якщо не знайдено
    v.success("contact_deleted", name=name)
    return True


@input_error
def delete_phone(args: list[str], book: AddressBook) -> bool:
    """Обробляє команду 'del-phone'. Видаляє телефон за індексом."""
    if len(args) != 2:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'del-phone'. Очікується: <ім'я> <індекс>")
    name, index_str = args
    try:
        index = int(index_str)
    except ValueError:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірний формат індексу у команді 'del-phone'. Індекс має бути числом.")

    record = book.find(name)
    record.remove_phone(index) # Кине PhoneException
    v.success("phone_deleted", name=name, index=index)
    return True


@input_error
def delete_email(args: list[str], book: AddressBook) -> bool:
    """Обробляє команду 'del-email'. Видаляє email за індексом."""
    if len(args) != 2:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'del-email'. Очікується: <ім'я> <індекс>")
    name, index_str = args
    try:
        index = int(index_str)
    except ValueError:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірний формат індексу у команді 'del-email'. Індекс має бути числом.")

    record = book.find(name)
    record.remove_email(index) # Кине EmailException
    v.success("email_deleted", name=name, index=index)
    return True


@input_error
def show_contact_details(args: list[str], book: AddressBook):
    """Обробляє команду 'phone'. Показує деталі контакту."""
    if len(args) != 1:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'phone'. Очікується: <ім'я>")
    name = args[0]
    record = book.find(name) # Кине ContactException
    v.show_contact(record)
    return False # Немає змін для збереження


@input_error
def show_all_handler(args: list[str], book: AddressBook):
    """Обробляє команду 'all'. Показує всі контакти."""
    if args: # Команда 'all' не повинна мати аргументів
        raise CommandException(ModelError.INVALID_COMMAND, message="Команда 'all' не приймає аргументів.")
    v.show_all_contacts(book)
    return False


# --- Команди для Дня Народження ---

@input_error
def add_birthday_handler(args: list[str], book: AddressBook) -> bool:
    """Обробляє 'add-birthday'/'add-bd'. Додає/змінює дату народження."""
    if len(args) != 2:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'add-birthday' або 'add-bd'. Очікується: <ім'я> <ДД.ММ.РРРР>")
    name, birthday_str = args
    record = book.find(name)
    # Додаємо/оновлюємо (може кинути BirthdayException)
    record.add_birthday(birthday_str)
    v.success("birthday_added", name=name, birthday=birthday_str)
    return True


@input_error
def show_birthday_handler(args: list[str], book: AddressBook):
    """Обробляє 'show-birthday'/'show-bd'. Показує дату народження."""
    if len(args) != 1:
        raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'show-birthday' або 'show-bd'. Очікується: <ім'я>")
    name = args[0]
    record = book.find(name)
    if record.birthday:
        v.info("contact_birthday", birthday_str=str(record.birthday))
    else:
        # Можна використати кастомний виняток або просто повідомити
        v.info("birthday_not_set", name=name) # Повідомлення про відсутність
        # або raise BirthdayException(ModelError.BIRTHDAY_NOT_SET, name=name) - якщо треба формально помилку
    return False


@input_error
def delete_birthday_handler(args: list[str], book: AddressBook) -> bool:
     """Обробляє 'del-birthday'/'del-bd'. Видаляє дату народження."""
     if len(args) != 1:
         raise CommandException(ModelError.INVALID_COMMAND, message="Невірна кількість аргументів для команди 'del-birthday' або 'del-bd'. Очікується: <ім'я>")
     name = args[0]
     record = book.find(name)
     record.remove_birthday() # Кине BirthdayException, якщо не встановлено
     v.success("birthday_deleted", name=name)
     return True


@input_error
def show_upcoming_birthdays_handler(args: list[str], book: AddressBook):
    """Обробляє 'birthdays'/'all-bd'. Показує найближчі дні народження."""
    days = 7 # За замовчуванням
    if args:
        try:
            days = int(args[0])
            if days <= 0:
                 raise ValueError("Кількість днів має бути позитивним числом.")
        except ValueError:
             raise CommandException(ModelError.INVALID_COMMAND, message="Невірний формат аргументу для команди 'birthdays' або 'all-bd'. Кількість днів має бути цілим позитивним числом.")

    upcoming = book.get_upcoming_birthdays(days)
    v.show_upcoming_birthdays(upcoming, days)
    return False


# --- Допоміжні команди ---

def hello_handler(*args, **kwargs): # Може приймати book, але не використовує
    """Обробляє 'hello'/'hi'."""
    v.say_hello()
    return False


def show_help_handler(*args, **kwargs):
    """Обробляє '?'/'help'."""
    v.show_help()
    return False


def clear_screen_handler(*args, **kwargs):
     """Обробляє 'clrscr'."""
     v.clear_screen()
     return False


def quit_handler(*args, **kwargs):
    """Обробляє 'exit'/'close'/'quit'. Завершує програму."""
    v.info("goodbye_message")
    exit(0) # Виконуємо вихід з програми


# ============================ СЛОВНИК КОМАНД ============================
# Використовуємо стиль з вирівнюванням

COMMANDS = {
    # Привітання
    'hello'          : hello_handler,
    'hi'             : hello_handler,
    'привіт'         : hello_handler,

    # Додавання (контакт/телефон/email)
    'add'            : add_contact,              # Додати контакт з телефоном / або телефон існуючому
    'add@'           : add_email_to_contact,     # Додати контакт з email / або email існуючому
    'add-email'      : add_email_to_contact,     # Аліас для add@
    'add-phone'      : add_extra_phone,          # Додати ще один телефон існуючому
    'add-email'      : add_extra_email,          # Ця логіка вже покрита в add_email_to_contact

    # Зміна
    'change'         : change_contact_field,     # Змінити телефон/email за індексом

    # Показ
    'phone'          : show_contact_details,     # Показати деталі контакту (замість 'show', 'contact')
    'all'            : show_all_handler,         # Показати всі контакти

    # Видалення
    'delete'         : delete_contact,           # Видалити контакт повністю
    'del-phone'      : delete_phone,             # Видалити телефон за індексом
    'del-email'      : delete_email,             # Видалити email за індексом

    # День народження
    'add-birthday'   : add_birthday_handler,     # Додати/змінити ДН
    'add-bd'         : add_birthday_handler,     # Аліас
    'show-birthday'  : show_birthday_handler,    # Показати ДН
    'show-bd'        : show_birthday_handler,    # Аліас
    'del-birthday'   : delete_birthday_handler,  # Видалити ДН
    'del-bd'         : delete_birthday_handler,  # Аліас
    'birthdays'      : show_upcoming_birthdays_handler, # Показати наступні ДН
    'all-bd'         : show_upcoming_birthdays_handler, # Аліас

    # Інші
    'clr'            : clear_screen_handler,     # Очистити екран
    '?'              : show_help_handler,        # Довідка
    'help'           : show_help_handler,        # Аліас
    'exit'           : quit_handler,             # Вихід
    'close'          : quit_handler,             # Аліас
    'quit'           : quit_handler,             # Аліас
}

# Список команд, які модифікують дані і потребують збереження
MODIFYING_COMMANDS = {
    'add', 'add@', 'add-email', 'add-phone',
    'change',
    'delete', 'del-phone', 'del-email',
    'add-birthday', 'add-bd',
    'del-birthday', 'del-bd',
}


# ============================ ГОЛОВНА ФУНКЦІЯ ВИКОНАННЯ ============================

def execute(command: str, args: list[str], book: AddressBook):
    """
    Знаходить та викликає відповідний обробник команди.
    Зберігає зміни, якщо команда модифікуюча.
    """
    handler = COMMANDS.get(command)
    if handler:
        result = handler(args, book=book)
        if result and command in MODIFYING_COMMANDS:
            mdl.save_contacts(book)
    else:
        # Використовуємо ключ з ModelError Enum та передаємо аргумент 'command'
        v.warn(ModelError.INVALID_COMMAND.value, command=command)
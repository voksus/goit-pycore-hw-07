import re
import json
from collections import UserDict
from datetime import datetime, date, timedelta
from enum import Enum

# ============================= ENUMS ТА КОНСТАНТИ =============================

class ModelError(Enum):
    """Перелік кодів помилок для моделі."""
    INVALID_COMMAND        = "invalid_command"
    INVALID_CONTACT_NAME   = "invalid_contact_name"
    INVALID_PHONE          = "invalid_phone"
    INVALID_EMAIL          = "invalid_email"
    INVALID_BIRTHDAY       = "invalid_birthday"
    CONTACT_EXISTS         = "contact_exists"
    CONTACT_NOT_FOUND      = "contact_not_found"
    DUPLICATE_PHONE        = "duplicate_phone"
    DUPLICATE_EMAIL        = "duplicate_email"
    PHONE_NOT_FOUND        = "phone_not_found"
    EMAIL_NOT_FOUND        = "email_not_found"
    BIRTHDAY_NOT_SET       = "birthday_not_set"
    EMPTY_CONTACTS         = "empty_contacts"
    INVALID_INDEX          = "invalid_index"
    EMPTY_CONTACT_FIELDS   = "empty_contact_fields"


# ============================= КЛАСИ ВИКЛЮЧЕНЬ =============================

class CommandException(Exception):
    """Базовий клас для винятків, пов'язаних з командами."""
    def __init__(self, error_code: ModelError, message="Помилка команди", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class ContactException(Exception):
    """Базовий клас для винятків, пов'язаних з контактами."""
    def __init__(self, error_code: ModelError, message="Помилка контакту", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class PhoneException(Exception):
    """Базовий клас для винятків, пов'язаних з телефонами."""
    def __init__(self, error_code: ModelError, message="Помилка телефону", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class EmailException(Exception):
    """Базовий клас для винятків, пов'язаних з email."""
    def __init__(self, error_code: ModelError, message="Помилка email", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)

class BirthdayException(Exception):
    """Базовий клас для винятків, пов'язаних з датою народження."""
    def __init__(self, error_code: ModelError, message="Помилка дати народження", **kwargs): # Додаємо **kwargs
        self.error_code = error_code
        self.kwargs = kwargs # Зберігаємо kwargs
        super().__init__(message)


# ============================= КЛАСИ ДАНИХ =============================

class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self._value}')"

class Name(Field):
    """Клас для зберігання та валідації імені контакту."""
    def __init__(self, value: str) -> None:
        if not self.validate(value):
             # Передаємо name
             raise ContactException(ModelError.INVALID_CONTACT_NAME, name=value)
        super().__init__(value)

    @staticmethod
    def validate(name: str) -> bool:
        """Перевіряє коректність імені."""
        return bool(re.fullmatch(r"[A-Za-zА-Яа-яІіЇїЄєҐґ' -]{1,50}", name)) # Додав пробіл та дефіс


class Phone(Field):
    """Клас для зберігання та валідації номера телефону."""
    def __init__(self, value: str) -> None:
        if not self.validate(value):
             # Передаємо phone
             raise PhoneException(ModelError.INVALID_PHONE, phone=value)
        super().__init__(value)

    @staticmethod
    def validate(phone: str) -> bool:
        """Перевіряє, чи телефон складається рівно з 10 цифр."""
        return bool(re.fullmatch(r"\d{10}", phone))


class Email(Field):
    """Клас для зберігання та валідації email."""
    def __init__(self, value: str) -> None:
        if not self.validate(value):
             # Передаємо email
             raise EmailException(ModelError.INVALID_EMAIL, email=value)
        super().__init__(value)

    @staticmethod
    def validate(email: str) -> bool:
        """Перевіряє базовий формат email."""
        return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}", email))


class Birthday(Field):
    """Клас для зберігання та валідації дати народження."""
    def __init__(self, value: str) -> None:
        try:
            parsed_date = datetime.strptime(value, '%d.%m.%Y').date()
            if parsed_date > date.today():
                 # Передаємо birthday
                 raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=value)
            super().__init__(parsed_date)
        except ValueError:
            # Передаємо birthday
            raise BirthdayException(ModelError.INVALID_BIRTHDAY, birthday=value)

    # перевизначимо сетер, щоб забезпечити валідацію при зміні
    @Field.value.setter
    def value(self, new_value: str):
        try:
            parsed_date = datetime.strptime(new_value, '%d.%m.%Y').date()
            if parsed_date > date.today():
                raise BirthdayException(ModelError.INVALID_BIRTHDAY, message=f"Дата народження не може бути в майбутньому: {new_value}")
            self._value = parsed_date
        except ValueError:
             raise BirthdayException(ModelError.INVALID_BIRTHDAY, message=f"Невірний формат дати народження: {new_value}. Використовуйте DD.MM.YYYY")

    def __str__(self) -> str:
        """Повертає дату у форматі DD.MM.YYYY."""
        return self.value.strftime('%d.%m.%Y')


# ============================= ЗАПИС КОНТАКТУ =============================

class Record:
    """Клас для представлення запису контакту в адресній книзі."""
    def __init__(self, name: str) -> None:
        """Ініціалізує запис з іменем та порожніми списками полів."""
        # Ім'я валідується при створенні об'єкта Name
        self.name: Name = Name(name)
        # Використовуємо списки для легшого керування індексами
        self.phones: list[Phone] = []
        self.emails: list[Email] = []
        self.birthday: Birthday | None = None

    # --- Робота з телефонами ---
    def add_phone(self, phone_str: str) -> None:
        """Додає телефон до контакту. Кидає PhoneException при помилках."""
        if any(p.value == phone_str for p in self.phones):
            # Передаємо name та phone для форматування
            raise PhoneException(ModelError.DUPLICATE_PHONE, name=self.name.value, phone=phone_str)
        # Валідація відбудеться при створенні Phone
        self.phones.append(Phone(phone_str))

    def edit_phone(self, index: int, new_phone_str: str) -> None:
        """Редагує телефон за індексом. Кидає PhoneException при помилках."""
        try:
            self.phones[index] = Phone(new_phone_str)
        except IndexError:
            # Передаємо name та index для форматування
            raise PhoneException(ModelError.PHONE_NOT_FOUND, name=self.name.value, index=index)
        except PhoneException as e: # Якщо Phone() кинув помилку формату
             e.kwargs['name'] = self.name.value # Додамо ім'я до існуючих kwargs
             raise e

    def remove_phone(self, index: int) -> None:
        """Видаляє телефон за індексом. Кидає PhoneException при помилці."""
        try:
            del self.phones[index]
        except IndexError:
            # Передаємо name та index
            raise PhoneException(ModelError.PHONE_NOT_FOUND, name=self.name.value, index=index)

    # --- Робота з email (аналогічно) ---
    def add_email(self, email_str: str) -> None:
        if any(e.value == email_str for e in self.emails):
            # Передаємо name та email
            raise EmailException(ModelError.DUPLICATE_EMAIL, name=self.name.value, email=email_str)
        self.emails.append(Email(email_str))

    def edit_email(self, index: int, new_email_str: str) -> None:
        try:
            self.emails[index] = Email(new_email_str)
        except IndexError:
            # Передаємо name та index
            raise EmailException(ModelError.EMAIL_NOT_FOUND, name=self.name.value, index=index)
        except EmailException as e: # Якщо Email() кинув помилку формату
             e.kwargs['name'] = self.name.value # Додамо ім'я
             raise e

    def remove_email(self, index: int) -> None:
        try:
            del self.emails[index]
        except IndexError:
            # Передаємо name та index
            raise EmailException(ModelError.EMAIL_NOT_FOUND, name=self.name.value, index=index)

    # --- Робота з днем народження (аналогічно) ---
    def add_birthday(self, birthday_str: str) -> None:
        try:
            self.birthday = Birthday(birthday_str)
        except BirthdayException as e:
             # Додамо name і birthday до kwargs винятку
             e.kwargs['name'] = self.name.value
             e.kwargs['birthday'] = birthday_str
             raise e # Перекидаємо виняток з доповненими kwargs

    def remove_birthday(self) -> None:
         if self.birthday is None:
             # Передаємо name
             raise BirthdayException(ModelError.BIRTHDAY_NOT_SET, name=self.name.value)
         self.birthday = None

    def __str__(self) -> str:
        """Повертає рядкове представлення запису."""
        phones_str = "; ".join(f"[{i}] {p.value}" for i, p in enumerate(self.phones)) or "Немає"
        emails_str = "; ".join(f"[{i}] {e.value}" for i, e in enumerate(self.emails)) or "Немає"
        birthday_str = str(self.birthday) if self.birthday else "Не вказано"
        return (f"Ім'я: {self.name.value}\n"
                f"  Телефони: {phones_str}\n"
                f"  Emails: {emails_str}\n"
                f"  День народження: {birthday_str}")


# ============================= АДРЕСНА КНИГА =============================

class AddressBook(UserDict):
    """Клас для представлення адресної книги."""

    def add_record(self, record: Record) -> None:
        if record.name.value in self.data:
            # Передаємо name
            raise ContactException(ModelError.CONTACT_EXISTS, name=record.name.value)
        self.data[record.name.value] = record

    def find(self, name: str) -> Record:
        record = self.data.get(name)
        if record is None:
            # Передаємо name
            raise ContactException(ModelError.CONTACT_NOT_FOUND, name=name)
        return record

    def delete(self, name: str) -> None:
        if name not in self.data:
            # Передаємо name
            raise ContactException(ModelError.CONTACT_NOT_FOUND, name=name)
        del self.data[name]

    def get_upcoming_birthdays(self, days: int = 7) -> list[dict[str, str]]:
        """
        Повертає список користувачів, яких потрібно привітати на наступному тижні.

        Args:
            days (int): Кількість днів наперед для перевірки (за замовчуванням 7).

        Returns:
            list[dict[str, str]]: Список словників з ім'ям та датою привітання.
                                   Приклад: [{'name': 'Ім'я', 'congratulation_date': 'DD.MM.YYYY'}]
        """
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday and record.birthday.value:
                bday: date = record.birthday.value
                # Переносимо дату народження на поточний рік
                birthday_this_year = bday.replace(year=today.year)

                # Якщо день народження вже минув цього року, розглядаємо наступний рік
                if birthday_this_year < today:
                    birthday_this_year = bday.replace(year=today.year + 1)

                # Порівнюємо з сьогоднішньою датою та інтервалом 'days'
                days_to_birthday = (birthday_this_year - today).days
                if 0 <= days_to_birthday < days:
                    # Визначаємо день тижня
                    weekday = birthday_this_year.weekday() # Пн=0..Нд=6

                    # Визначаємо дату привітання (переносимо з вихідних на Пн)
                    congratulation_date = birthday_this_year
                    if weekday >= 5: # Сб або Нд
                        days_to_monday = 7 - weekday
                        congratulation_date += timedelta(days=days_to_monday)

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime('%d.%m.%Y'),
                        "birthday_date": bday.strftime('%d.%m.%Y'), # Додамо реальну дату для інформації
                        "original_weekday": birthday_this_year.weekday() # Для можливого відображення дня тижня
                    })
        # Сортуємо за датою привітання
        upcoming_birthdays.sort(key=lambda x: datetime.strptime(x['congratulation_date'], '%d.%m.%Y').date())
        return upcoming_birthdays


# ============================= СЕРІАЛІЗАЦІЯ =============================

DEFAULT_FILENAME = "contacts.json"

def save_contacts(book: AddressBook, filename: str = DEFAULT_FILENAME) -> None:
    """Зберігає адресну книгу у файл JSON."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            data_to_save = {}
            for name, record in book.data.items():
                record_data = {
                    "phones": [phone.value for phone in record.phones],
                    "emails": [email.value for email in record.emails],
                    # Зберігаємо день народження, якщо він є
                    "birthday": str(record.birthday) if record.birthday else None
                }
                data_to_save[name] = record_data
            json.dump(data_to_save, file, indent=4, ensure_ascii=False)
    except IOError as e:
        # Тут можна або прокинути далі, або обробити (напр., записати в лог)
        # Поки просто виведемо помилку, щоб бачити проблеми запису
        print(f"Помилка збереження файлу '{filename}': {e}")


def load_contacts(filename: str = DEFAULT_FILENAME) -> AddressBook:
    """Завантажує адресну книгу з файлу JSON."""
    book = AddressBook()
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            for name, entry in data.items():
                try:
                    # Створюємо запис (може кинути ContactException)
                    record = Record(name)

                    # Додаємо телефони (може кинути PhoneException)
                    for phone in entry.get("phones", []):
                        try:
                            record.add_phone(phone)
                        # Ловимо PhoneException і EmailException, бо вони можуть бути під час завантаження старих даних
                        except (PhoneException, EmailException) as e:
                            # Логуємо некоректні/дублікати телефонів при завантаженні
                            print(f"Попередження при завантаженні: проігноровано телефон '{phone}' для '{name}'. Причина: {e.error_code.value}")

                    # Додаємо email (може кинути EmailException)
                    for email in entry.get("emails", []):
                        try:
                            record.add_email(email)
                        # Ловимо PhoneException і EmailException
                        except (PhoneException, EmailException) as e:
                            print(f"Попередження при завантаженні: проігноровано email '{email}' для '{name}'. Причина: {e.error_code.value}")

                    # Додаємо день народження (може кинути BirthdayException)
                    birthday_str = entry.get("birthday")
                    if birthday_str:
                        try:
                            record.add_birthday(birthday_str)
                        except BirthdayException as e:
                             print(f"Попередження при завантаженні: проігноровано дату народження '{birthday_str}' для '{name}'. Причина: {e.error_code.value}")

                    # Додаємо валідний запис до книги (може кинути ContactException, хоча не повинен при чистому завантаженні)
                    book.add_record(record)

                except ContactException as e:
                    print(f"Помилка завантаження запису для імені '{name}': {e.error_code.value}. Запис пропущено.")

    except FileNotFoundError:
        # Це нормально, якщо файл ще не створено
        print(f"Файл контактів '{filename}' не знайдено. Буде створено новий при збереженні.")
    except json.JSONDecodeError:
        print(f"Помилка: Файл контактів '{filename}' пошкоджено або має невірний формат JSON.")
    except IOError as e:
         print(f"Помилка читання файлу '{filename}': {e}")

    return book
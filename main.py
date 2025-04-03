import controller as ctrl
import model as mdl
import view as v # Додаємо імпорт view для доступу до clear_screen

def main():
    """Головна функція додатку."""
    # Очищення екрану та привітання
    v.clear_screen()

    # Завантаження контактів відбувається тут
    contacts = mdl.load_contacts(mdl.DEFAULT_FILENAME)
    ctrl.hello_handler() # Викликаємо обробник напряму

    while True:
        try:
            # Отримуємо команду від користувача
            user_input = v.ask()
            if not user_input: # Пропускаємо порожній ввід
                v.cursor_up(1) # ...повертаючи курсор на рядок назад вгору
                continue

            # Парсимо команду та аргументи
            command, args = ctrl.parse_input(user_input)

            # Виконуємо команду (quit_handler обробить вихід)
            ctrl.execute(command, args, contacts)

        except KeyboardInterrupt:
            # Обробка Ctrl+C для коректного виходу
            ctrl.quit_handler() # Викликаємо той самий обробник виходу

if __name__ == "__main__":
    main()
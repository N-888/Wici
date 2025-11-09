# ============================================================
# 📘 ПРОГРАММА: Автоматизированный поиск и навигация по статьям Википедии в Консоли.
# 📌 Технологии: Selenium + Firefox + GeckoDriver (автоматическая установка)
# 🧠 Автор: N-888
# ============================================================

# --- Импорт системных и сетевых библиотек ---
import time               # Для задержек (имитация «человеческого» поведения)
import random             # Для случайного выбора ссылок
import platform           # Чтобы определить архитектуру системы (win32 или win64)
import urllib.request     # Для загрузки драйвера GeckoDriver вручную, если автозагрузка не сработает
import zipfile            # Для распаковки zip-архива
import os                 # Для работы с путями и файлами
import subprocess          # Для проверки версии драйвера через консоль

# --- Импорт Selenium и автоматического загрузчика GeckoDriver ---
from selenium import webdriver
from selenium.webdriver.common.by import By  # Для поиска элементов на странице
import geckodriver_autoinstaller  # noqa  # Для автоматической проверки и установки GeckoDriver

# ==========================================================
# 🔧 ФУНКЦИЯ 1. Автоматическая установка и обновление GeckoDriver + проверка совместимости с Firefox
# ==========================================================
def setup_geckodriver():
    """Проверяет наличие GeckoDriver, сверяет с актуальной версией на GitHub и обновляет при необходимости"""
    import re
    import json

    try:
        print("🔍 Проверяю наличие и актуальность GeckoDriver...")

        # 1️⃣ Определяем последнюю версию GeckoDriver с GitHub API
        github_api = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
        with urllib.request.urlopen(github_api, timeout=10) as response:
            data = json.load(response)
            latest_version = data["tag_name"].replace("v", "").strip()

        # 2️⃣ Определяем текущую версию Firefox
        try:
            firefox_proc = subprocess.run(["firefox", "--version"], capture_output=True, text=True)
            firefox_match = re.search(r"(\d+\.\d+)", firefox_proc.stdout)
            firefox_version = firefox_match.group(1) if firefox_match else "не определена"
            print(f"🦊 Найдена версия Firefox: {firefox_version}")
        except (FileNotFoundError, subprocess.SubprocessError):
            firefox_version = "не найден"
            print("⚠️ Firefox не найден или не доступен для проверки.")

        # 3️⃣ Проверяем, установлен ли уже geckodriver
        current_driver_path = None
        for path in os.getenv("PATH", "").split(os.pathsep):
            possible_driver = os.path.join(path, "geckodriver.exe")
            if os.path.exists(possible_driver):
                current_driver_path = possible_driver
                break

        def get_local_version(driver_path):
            """Определяет локальную версию geckodriver через вызов --version"""
            try:
                proc_result = subprocess.run([driver_path, "--version"], capture_output=True, text=True)
                match_obj = re.search(r"geckodriver (\d+\.\d+\.\d+)", proc_result.stdout)
                return match_obj.group(1) if match_obj else None
            except (subprocess.SubprocessError, FileNotFoundError):
                return None

        local_version = get_local_version(current_driver_path) if current_driver_path else None

        # 4️⃣ Если драйвера нет или версия устарела → обновляем
        if not local_version or local_version != latest_version:
            print(f"⏬ Устанавливаю последнюю версию GeckoDriver ({latest_version})...")
            arch = "win64" if platform.machine().endswith("64") else "win32"
            zip_url = f"https://github.com/mozilla/geckodriver/releases/download/v{latest_version}/geckodriver-v{latest_version}-{arch}.zip"
            zip_path = "geckodriver.zip"

            urllib.request.urlretrieve(zip_url, zip_path)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)
            time.sleep(1)

            print(f"✅ GeckoDriver {latest_version} успешно установлен!\n")
        else:
            print(f"✅ GeckoDriver уже актуальной версии ({local_version}).\n")

        # 5️⃣ Проверяем совместимость GeckoDriver и Firefox
        if firefox_version != "не найден":
            print("🔧 Проверяю совместимость GeckoDriver с Firefox...")
            driver_major = local_version.split(".")[0] if local_version else "0"
            firefox_major = firefox_version.split(".")[0] if firefox_version != "не определена" else "0"
            if abs(int(driver_major) - int(firefox_major)) <= 5:
                print("🟢 GeckoDriver совместим с текущей версией Firefox.\n")
            else:
                print("🟡 Версии GeckoDriver и Firefox могут быть несовместимы. Рекомендуется обновить Firefox!\n")

        time.sleep(1)

    except (OSError, ValueError) as e:
        print(f"⚠️ Ошибка при установке или проверке GeckoDriver: {e}")
        print("🚨 Попробуй перезапустить программу с доступом к интернету.")
        exit()

# ==========================================================
# 💾 ФУНКЦИИ 2. Работа с сохранением последнего запроса
# ==========================================================
def save_last_query(query):
    """Сохраняет последний запрос в файл"""
    try:
        with open("last_query.txt", "w", encoding="utf-8") as f:
            f.write(query.strip())
    except (IOError, OSError) as e:  # 🔥 Конкретные исключения
        print(f"⚠️ Не удалось сохранить последний запрос: {e}")

def load_last_query():
    """Загружает последний запрос, если он есть"""
    if os.path.exists("last_query.txt"):
        try:
            with open("last_query.txt", "r", encoding="utf-8") as f:
                last_query = f.read().strip()
                return last_query if last_query else None
        except (OSError, UnicodeError) as e:
            print(f"⚠️ Не удалось загрузить last_query.txt: {e}")
            return None
    return None

# ==========================================================
# 🔎 ФУНКЦИЯ 3. Поиск статьи на Википедии (реальный поиск)
# ==========================================================
def open_article(browser, query):
    """Открывает статью Википедии по запросу пользователя через поиск"""
    base_url = "https://ru.wikipedia.org"
    browser.get(base_url)
    time.sleep(2)

    try:
        search_box = browser.find_element(By.NAME, "search")
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(3)

        if "страницы, соответствующие запросу" in browser.page_source.lower() or "результаты поиска" in browser.title.lower():
            print("⚠️ Статья не найдена. Вот несколько похожих вариантов:")
            results = browser.find_elements(By.CSS_SELECTOR, "ul.mw-search-results li a")
            suggestions = []
            for a in results[:10]:
                title = a.text.strip()
                href = a.get_attribute("href")
                if title and href:
                    suggestions.append((title, href))

            if not suggestions:
                print("❌ Похожие статьи не найдены. Попробуй другой запрос.\n")
                return False

            for i, (title, _) in enumerate(suggestions, start=1):
                print(f"{i}. {title}")

            choice = input("👉 Введи номер нужной статьи (1–10) или 'н' для отмены: ").strip()
            if choice.lower() == "н":
                print("↩️ Отмена выбора. Возвращаемся в меню.")
                return False

            if not choice.isdigit() or not (1 <= int(choice) <= len(suggestions)):
                print("⚠️ Некорректный выбор. Попробуй снова.")
                return False

            _, link = suggestions[int(choice) - 1]
            browser.get(link)
            time.sleep(3)
        else:
            time.sleep(2)

        title_text = browser.title
        if "википедия" not in title_text.lower():
            print("⚠️ Ошибка: страница не похожа на статью Википедии. Попробуй другой запрос.")
            return False

        print(f"📖 Открыта статья: {title_text}\n")
        save_last_query(query)
        time.sleep(4)
        return True

    except Exception as e:
        print(f"🚨 Ошибка при загрузке статьи: {e}")
        time.sleep(3)
        return False

# ==========================================================
# 📜 ФУНКЦИЯ 4. Листание параграфов/ абзацев статьи
# ==========================================================
def read_paragraphs(browser, query):
    """Выводит параграфы текущей статьи"""
    paragraphs = browser.find_elements(By.TAG_NAME, "p")
    time.sleep(3)
    if not paragraphs:
        print("❌ Параграфы не найдены на странице.")
        time.sleep(3)
        return

    print(f"📜 Листаем параграфы статьи по запросу: «{query}»")
    print("Нажимай Enter для следующего параграфа или 'н' для выхода.\n")
    time.sleep(3)
    for p in paragraphs:
        user_input = input(f"{p.text}\n\n➡️ Продолжить? (Enter / н): ")
        time.sleep(3)
        if user_input.lower() == "н":
            break

# ==========================================================
# 🔗 ФУНКЦИЯ 5. Переход на случайную связанную статью
# ==========================================================
def go_to_random_link(browser):
    """Переходит на случайную связанную статью"""
    links = browser.find_elements(By.TAG_NAME, "a")
    valid_links = [
        a for a in links if a.get_attribute("href") and "/wiki/" in a.get_attribute("href")
    ]
    time.sleep(3)

    if not valid_links:
        print("❌ Связанных страниц не найдено.")
        time.sleep(3)
        return False

    chosen = random.choice(valid_links)
    link = chosen.get_attribute("href")
    print(f"🎲 Переход на случайную связанную статью: {link}\n")
    time.sleep(3)

    browser.get(link)
    time.sleep(2)
    print(f"📘 Теперь открыта: {browser.title}\n")
    time.sleep(3)
    return True

# ==========================================================
# 🧭 ФУНКЦИЯ 6. Ручной выбор одной из 10 связанных статей
# ==========================================================
def choose_related_article(browser):
    """Показывает до 10 связанных ссылок и даёт выбрать нужную"""
    links = browser.find_elements(By.TAG_NAME, "a")
    valid_links = [
        a for a in links
        if a.get_attribute("href")
        and "/wiki/" in a.get_attribute("href")
        and not any(x in a.get_attribute("href") for x in [":", "#"])
    ]

    if not valid_links:
        print("❌ Связанных статей не найдено.")
        time.sleep(5)
        return False

    unique_links = []
    for a in valid_links:
        title = a.text.strip()
        href = a.get_attribute("href")
        if title and href not in [u[1] for u in unique_links]:
            unique_links.append((title, href))
        if len(unique_links) >= 10:
            break

    print("\n📚 Найдено несколько связанных статей:")
    for i, (title, _) in enumerate(unique_links, start=1):
        print(f"{i}. {title}")
        time.sleep(3)

    choice = input("👉 Введи номер нужной статьи (1–10) или 'н' для отмены: ").strip()
    if choice.lower() == "н":
        print("↩️ Отмена выбора. Возвращаемся в меню.")
        time.sleep(3)
        return False

    if not choice.isdigit() or not (1 <= int(choice) <= len(unique_links)):
        print("⚠️ Некорректный выбор. Попробуй снова.")
        time.sleep(3)
        return False

    _, link = unique_links[int(choice) - 1]
    print(f"🔗 Переход по выбранной ссылке: {link}\n")
    browser.get(link)
    time.sleep(3)
    print(f"📘 Теперь открыта: {browser.title}\n")
    time.sleep(3)
    return True

# ==========================================================
# 🚀 ОСНОВНАЯ ПРОГРАММА
# ==========================================================
def main():
    """Основная логика программы"""
    setup_geckodriver()

    print("🌍 Добро пожаловать в консольную интерактивную Википедию на Python!")
    time.sleep(3)

    last_query = load_last_query()
    if last_query:
        choice = input(f"💾 Найден предыдущий запрос: «{last_query}». Продолжить с него? (д/н): ").lower()
        time.sleep(3)
        if choice == "д":
            query = last_query
        else:
            query = input("🔎 Введи новый запрос для поиска: ").strip()
            time.sleep(3)
    else:
        query = input("🔎 Введи запрос для поиска: ").strip()
        time.sleep(3)

    browser = webdriver.Firefox()
    browser.maximize_window()

    if not open_article(browser, query):
        browser.quit()
        return

    # Основной цикл взаимодействия
    while True:
        print("\n✨ Что хочешь сделать дальше?")
        print("А — 📜 Листать параграфы / абзацы текущей статьи по последнему запросу")
        print("Б — 🎲 Перейти на случайную связанную статью последнего запроса")
        print("В — 📚 Выбрать связанную статью вручную из списка до 10 вариантов")
        print("Г — 🧠 Ввести новый запрос для поиска")
        print("Д — 🚪 Выйти из программы")

        action = input("👉 Твой выбор (А/Б/В/Г/Д): ").lower()
        time.sleep(12)

        if action == "а":
            read_paragraphs(browser, query)
            time.sleep(5)
        elif action == "б":
            go_to_random_link(browser)
            time.sleep(5)
        elif action == "в":
            choose_related_article(browser)
            time.sleep(5)
        elif action == "г":
            new_query = input("🧠 Введи новый запрос для поиска: ").strip()
            query = new_query
            open_article(browser, query)
            time.sleep(5)
        elif action == "д":
            print("👋 До встречи! Браузер закрыт.")
            browser.quit()
            time.sleep(3)
            break
        else:
            print("⚠️ Некорректный выбор. Попробуй снова.")
            time.sleep(3)

# ==========================================================
# 🚀 ЗАПУСК ПРОГРАММЫ
# ==========================================================
if __name__ == "__main__":
    main()
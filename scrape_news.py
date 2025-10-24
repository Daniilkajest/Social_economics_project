import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

NEWS_URL = "https://ria.ru/lenta/"

def get_latest_headlines(limit=100):
    print("--- Запускаем Selenium для парсинга РИА Новости (v. final) ---")

    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless')

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Браузер Chrome запущен в фоновом режиме.")

    headlines = []
    try:
        print(f"Открываем страницу: {NEWS_URL}")
        driver.get(NEWS_URL)

        print("Ждем, пока на странице появятся новости (до 30 секунд)...")
        # Ждем появления именно ссылки, содержащей заголовок. Это надежнее.
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.list-item__title")))
        print("✅ Заголовки новостей на странице обнаружены!")

        time.sleep(1)
        html_content = driver.page_source

        soup = BeautifulSoup(html_content, 'html.parser')

        # --- ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ СЕЛЕКТОРОВ ---
        # Будем искать сразу ссылки с заголовками
        title_tags = soup.select('a.list-item__title')

        for title_tag in title_tags[:limit]:
            # Родительский элемент, в котором лежит и заголовок, и время
            parent_item = title_tag.find_parent('div', class_='list-item')
            if not parent_item:
                continue # Если не нашли родителя, пропускаем эту новость

            time_tag = parent_item.find('div', class_='list-item__date')

            if title_tag and time_tag:
                title = title_tag.text.strip()
                url = "https://ria.ru" + title_tag['href']
                time_str = time_tag.text.strip()

                headlines.append({'time': time_str, 'title': title, 'url': url})
        # ------------------------------------

        print(f"✅ Успешно собрано {len(headlines)} заголовков.")
        return headlines

    except Exception as e:
        print(f"❌ Произошла ошибка во время работы Selenium: {e}")
        return []
    finally:
        print("Закрываем браузер...")
        driver.quit()

if __name__ == '__main__':
    print("--- Тестовый запуск парсера (финальная версия) ---")
    latest_news = get_latest_headlines(10)

    if latest_news:
        print("\n--- Последние 10 новостей ---")
        for i, news in enumerate(latest_news, 1):
            print(f"{i}. {news['time']} - {news['title']}")

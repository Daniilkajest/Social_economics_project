import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
from tqdm import tqdm

# --- НАСТРОЙКИ ---
URL = "https://znanierussia.ru/articles/Список-Героев-Российской-Федерации"
DB_TABLE_NAME = 'russian_heroes' # Название для новой таблицы в БД

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БД (скопируй из другого скрипта) ---
db_user = 'postgres'
db_password = 'glavvrach228007'
db_host = 'localhost'
db_port = '5432'
db_name = 'social_economics'

def scrape_and_process_heroes():
    """Скрапит, очищает и агрегирует данные о Героях России."""
    try:
        print(f"Скачиваем страницу: {URL}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Находим все таблицы на странице. Нужная нам - обычно одна из первых и самая большая.
        # Мы будем искать таблицу, содержащую специфический заголовок, например, "Фамилия, имя, отчество"
        tables = soup.find_all('table', {'class': 'standard'})
        if not tables:
            print("❌ Не удалось найти таблицы на странице.")
            return None

        print(f"Найдено {len(tables)} таблиц. Ищем нужную...")
        target_table = None
        for table in tables:
            if 'Фамилия' in table.text:
                target_table = table
                break

        if not target_table:
            print("❌ Не удалось найти таблицу с данными о героях.")
            return None

        print("✅ Найдена таблица с героями. Начинаем парсинг строк...")

        all_heroes = []
        # Находим все строки таблицы, пропуская заголовок (tr ~ table row)
        rows = target_table.find_all('tr')[1:]

        for row in tqdm(rows, desc="Обработка записей"):
            # Находим все ячейки в строке (td ~ table data)
            cols = row.find_all('td')

            # Проверяем, что в строке достаточно ячеек
            if len(cols) > 3:
                fio = cols[0].text.strip()
                decree_date_str = cols[2].text.strip()
                region = cols[3].text.strip()

                # Попробуем извлечь год из даты
                try:
                    # Дата может быть в формате "ДД.ММ.ГГГГ"
                    year = int(decree_date_str.split('.')[-1])
                    if year >= 2001:
                        all_heroes.append({'fio': fio, 'year': year, 'region': region})
                except (ValueError, IndexError):
                    # Если не можем распознать год, пропускаем запись
                    continue

        if not all_heroes:
            print("⚠️ Не удалось собрать данные о героях 21 века.")
            return None

        print(f"\n✅ Собрано {len(all_heroes)} записей о героях, награжденных с 2001 года.")

        # --- Агрегация данных ---
        df = pd.DataFrame(all_heroes)

        # Считаем количество героев по регионам
        heroes_by_region = df['region'].value_counts().reset_index()
        heroes_by_region.columns = ['region', 'heroes_count_21_century']

        return heroes_by_region

    except requests.RequestException as e:
        print(f"❌ Ошибка при скачивании страницы: {e}")
        return None
    except Exception as e:
        print(f"❌ Произошла непредвиденная ошибка: {e}")
        return None


if __name__ == '__main__':
    heroes_df = scrape_and_process_heroes()

    if heroes_df is not None:
        print("\n--- Топ-15 регионов по количеству Героев России (с 2001 г.) ---")
        print(heroes_df.head(15))

        # --- Сохранение в CSV ---
        output_filename = 'russian_heroes_by_region.csv'
        heroes_df.to_csv(output_filename, index=False, encoding='utf-8')
        print(f"\n✅ Результаты сохранены в файл: '{output_filename}'")

        # --- Загрузка в PostgreSQL ---
        try:
            print(f"\n--- Загружаем данные в таблицу '{DB_TABLE_NAME}' в PostgreSQL ---")
            engine = create_engine(f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

            # Загружаем с 'replace', чтобы при каждом запуске таблица полностью перезаписывалась
            heroes_df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)

            print("✅ Данные успешно загружены в базу данных!")
        except Exception as e:
            print(f"❌ Ошибка при загрузке в базу данных: {e}")

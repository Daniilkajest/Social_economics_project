import pandas as pd
from sqlalchemy import create_engine

# --- НАСТРОЙКИ ---
CSV_FILENAME = 'data/casualties_by_region.csv' # Путь к нашему новому файлу
DB_TABLE_NAME = 'casualties_regions' # Дадим таблице новое, более понятное имя

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БД ---
db_user = 'postgres'
db_password = 'glavvrach228007' # <--- НЕ ЗАБУДЬ ЗАМЕНИТЬ
db_host = 'localhost'
db_port = '5432'
db_name = 'social_economics'

# Словарь для исправления названий регионов
# Ключ - как в CSV, Значение - как в данных Росстата
region_name_mapping = {
    'Санкт-Петербург': 'Санкт-Петербург', # Для г. Санкт-Петербург, если он так записан
    'Москва': 'Москва', # Для г. Москва
    'Республика Крым': 'Республика Крым',
    'Севастополь': 'Севастополь',
    'Республика Северная Осетия-Алания': 'Республика Северная Осетия – Алания',
    'Ханты-Мансийский автономный округ - Югра': 'Ханты-Мансийский автономный округ – Югра',
    'Кемеровская область': 'Кемеровская область', # Предполагаем, что в CSV уже нет "-Кузбасс"
    # Добавляем исправления для городов федерального значения из предыдущего шага
    'г. Москва': 'Москва',
    'г. Санкт-Петербург': 'Санкт-Петербург',
    'г. Севастополь': 'Севастополь',
}


def load_casualties_from_csv_to_db():
    try:
        # --- 1. Читаем CSV-файл ---
        print(f"Читаем данные из файла: '{CSV_FILENAME}'...")
        df = pd.read_csv(CSV_FILENAME)
        df = df.rename(columns={'value': 'casualties_count'}) # Переименуем колонку
        print("✅ Файл успешно прочитан.")

        # --- 2. ОЧИСТКА И ИСПРАВЛЕНИЕ ДАННЫХ ---
        # Удаляем строки, которые не являются регионами РФ
        regions_to_drop = ['###', 'Иностранцы', 'ЛНР', 'ДНР']
        df = df[~df['region'].isin(regions_to_drop)]

        # Применяем исправления названий из словаря
        df['region'] = df['region'].replace(region_name_mapping)
        print("✅ Названия регионов исправлены.")

        # --- 3. ЗАГРУЗКА В БД ---
        print("Подключаемся к базе данных PostgreSQL...")
        engine = create_engine(f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        print(f"Загружаем данные в таблицу '{DB_TABLE_NAME}'...")
        df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)

        print(f"\n✅✅✅ Успех! Данные из CSV загружены в таблицу '{DB_TABLE_NAME}'.")

    except FileNotFoundError:
        print(f"❌ ОШИБКА: Файл '{CSV_FILENAME}' не найден. Убедитесь, что вы положили его в папку 'data' и правильно переименовали.")
    except Exception as e:
        print(f"❌ Произошла непредвиденная ошибка: {e}")

if __name__ == '__main__':
    load_casualties_from_csv_to_db()

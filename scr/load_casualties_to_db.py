import pandas as pd
from sqlalchemy import create_engine

# --- НАСТРОЙКИ ДЛЯ ЛОКАЛЬНОЙ БД ---
DB_USER = "postgres"
DB_PASSWORD = "glavvrach228007"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "social_economics"

# --- НАСТРОЙКИ ДАННЫХ ---
CSV_FILENAME = 'data/casualties_by_region.csv'
DB_TABLE_NAME = 'casualties_regions'

# Словарь для исправления названий
region_name_mapping = {
    'г. Москва': 'Москва',
    'г. Санкт-Петербург': 'Санкт-Петербург',
    'г. Севастополь': 'Севастополь',
    'Республика Северная Осетия-Алания': 'Республика Северная Осетия – Алания',
    'Ханты-Мансийский автономный округ - Югра': 'Ханты-Мансийский автономный округ – Югра',
    'Кемеровская область - Кузбасс': 'Кемеровская область',
}

def load_casualties_from_csv_to_db():
    try:
        df = pd.read_csv(CSV_FILENAME)
        df = df.rename(columns={'value': 'casualties_count'})
        regions_to_drop = ['###', 'Иностранцы', 'ЛНР', 'ДНР']
        df = df[~df['region'].isin(regions_to_drop)]
        df['region'] = df['region'].replace(region_name_mapping)

        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        print(f"Загружаем данные в таблицу '{DB_TABLE_NAME}'...")
        df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)
        print(f"\n✅ Успех! Данные из CSV загружены в таблицу '{DB_TABLE_NAME}'.")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")

if __name__ == '__main__':
    load_casualties_from_csv_to_db()

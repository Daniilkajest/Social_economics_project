import pandas as pd
from sqlalchemy import create_engine

# --- НАСТРОЙКИ ДЛЯ ЛОКАЛЬНОЙ БД ---
DB_USER = "postgres"
DB_PASSWORD = "glavvrach228007"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "social_economics"

# --- НАСТРОЙКИ ДАННЫХ ---
CSV_FILENAME = 'hh_vacancies_by_city.csv'
DB_TABLE_NAME = 'hh_vacancies'

def load_hh_data_to_db():
    try:
        df = pd.read_csv(CSV_FILENAME)
        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
        print(f"Загружаем данные в таблицу '{DB_TABLE_NAME}'...")
        df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)
        print(f"\n✅ Успех! Данные о вакансиях загружены в таблицу '{DB_TABLE_NAME}'.")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")

if __name__ == '__main__':
    load_hh_data_to_db()

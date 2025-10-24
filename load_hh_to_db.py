import pandas as pd
from sqlalchemy import create_engine

# --- НАСТРОЙКИ ---
# Имя файла, который создал наш парсер hh.ru
CSV_FILENAME = 'hh_vacancies_by_city.csv'
# Название для новой таблицы в базе данных
DB_TABLE_NAME = 'hh_vacancies'

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БД (те же, что и раньше) ---
db_user = 'postgres'
db_password = 'glavvrach228007' # <--- НЕ ЗАБУДЬ ЗАМЕНИТЬ
db_host = 'localhost'
db_port = '5432'
db_name = 'social_economics'

def load_hh_data_to_db():
    """
    Читает CSV-файл с данными от HeadHunter и загружает его
    в новую таблицу в базе данных PostgreSQL.
    """
    try:
        # --- 1. Читаем CSV-файл ---
        print(f"Читаем данные из файла: '{CSV_FILENAME}'...")
        df = pd.read_csv(CSV_FILENAME)
        print("✅ Файл успешно прочитан.")

        # --- 2. Подключаемся к БД ---
        print("Подключаемся к базе данных PostgreSQL...")
        engine = create_engine(f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        # --- 3. Загружаем данные в новую таблицу ---
        print(f"Загружаем данные в таблицу '{DB_TABLE_NAME}'...")
        # Используем if_exists='replace', чтобы при каждом запуске скрипта
        # таблица полностью перезаписывалась свежими данными.
        df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)

        print(f"\n✅✅✅ Успех! Данные о вакансиях загружены в таблицу '{DB_TABLE_NAME}'.")

    except FileNotFoundError:
        print(f"❌ ОШИБКА: Файл '{CSV_FILENAME}' не найден. Убедитесь, что вы сначала запустили скрипт 'scrape_hh.py'.")
    except Exception as e:
        print(f"❌ Произошла непредвиденная ошибка: {e}")


if __name__ == '__main__':
    load_hh_data_to_db()

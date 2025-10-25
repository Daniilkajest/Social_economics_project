import pandas as pd
import glob
import os
from sqlalchemy import create_engine

# --- НАСТРОЙКИ ДЛЯ ЛОКАЛЬНОЙ БД ---
DB_USER = "postgres"
DB_PASSWORD = "glavvrach228007" # Твой пароль от локального Postgres
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "social_economics" # Имя твоей локальной базы

# --- НАСТРОЙКИ ДАННЫХ ---
TABLE_NAME = 'rosstat_data' # Имя таблицы, куда будем грузить
DATA_FOLDER_PATH = 'data'

def load_all_csv_to_db():
    try:
        engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

        csv_files = glob.glob(os.path.join(DATA_FOLDER_PATH, '*.csv'))
        if not csv_files:
            print(f"ОШИБКА: В папке '{DATA_FOLDER_PATH}' нет CSV-файлов.")
            return

        print(f"Найдено {len(csv_files)} файлов. Начинаем загрузку в таблицу '{TABLE_NAME}'...")

        first_file = True
        for i, file_path in enumerate(csv_files):
            df_part = pd.read_csv(file_path, sep=';')
            write_mode = 'replace' if first_file else 'append'
            df_part.to_sql(TABLE_NAME, engine, if_exists=write_mode, index=False)
            print(f"  ({i+1}/{len(csv_files)}) Файл '{os.path.basename(file_path)}' загружен.")
            first_file = False

        print(f"\n✅✅✅ Все файлы загружены в таблицу '{TABLE_NAME}'!")

    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")

if __name__ == '__main__':
    load_all_csv_to_db()

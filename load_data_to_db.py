import pandas as pd
import glob
import os
from sqlalchemy import create_engine

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К ОБЛАЧНОЙ БД ---
db_user = 'postgres'
db_password = 'Glavvrach228007' # <-- Самое важное!
db_host = 'db.hqylrohffotpuzjqwbc.supabase.co' # <-- Из строки подключения
db_port = '5432' # <-- Из строки подключения
db_name = 'postgres' # <-- Из строки подключения

# --- 2. НАСТРОЙКИ ПУТИ К ДАННЫМ ---
# Этот скрипт ожидает, что рядом с ним есть папка 'data', в которой лежат все CSV.
data_folder_path = 'data'

# --- 3. ОСНОВНАЯ ЛОГИКА СКРИПТА (ETL-процесс) ---
def load_all_csv_to_db():
    """
    Эта функция находит все CSV-файлы в указанной папке,
    читает их по очереди и загружает в единую таблицу в базе данных PostgreSQL.
    """
    try:
        # Создаем "движок" для подключения к базе данных
        engine = create_engine(f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        print("Начинаем процесс загрузки данных в PostgreSQL...")

        # Находим все CSV-файлы в папке 'data'
        csv_files = glob.glob(os.path.join(data_folder_path, '*.csv'))

        if not csv_files:
            print(f"❌ ОШИБКА: В папке '{data_folder_path}' не найдено CSV-файлов. Убедитесь, что они там лежат.")
            return

        print(f"Найдено {len(csv_files)} файлов. Начинаем загрузку в таблицу '{table_name}'...")
        print("Это может занять несколько минут...")

        # Флаг для первой загрузки
        first_file = True

        # Перебираем все найденные файлы в цикле
        for i, file_path in enumerate(csv_files):
            # Читаем очередной CSV-файл в DataFrame
            df_part = pd.read_csv(file_path, sep=';')

            # Определяем, как загружать данные:
            # - Для первого файла используем 'replace', чтобы таблица была создана заново (гарантия чистоты).
            # - Для всех последующих используем 'append', чтобы добавить данные в уже существующую таблицу.
            if first_file:
                write_mode = 'replace'
                first_file = False
            else:
                write_mode = 'append'

            # Загружаем DataFrame в таблицу SQL
            df_part.to_sql(table_name, engine, if_exists=write_mode, index=False)

            print(f"  ({i+1}/{len(csv_files)}) Файл '{os.path.basename(file_path)}' успешно загружен.")

        print(f"\n✅✅✅ Все {len(csv_files)} файлов успешно загружены в таблицу '{table_name}' в базе данных '{db_name}'! ✅✅✅")

    except Exception as e:
        print(f"\n❌ Произошла ошибка во время выполнения скрипта: {e}")

# --- 4. ТОЧКА ВХОДА В СКРИПТ ---
if __name__ == '__main__':
    # Эта стандартная конструкция в Python означает:
    # "Если этот файл запускается напрямую (а не импортируется в другой файл),
    # то выполнить функцию load_all_csv_to_db()"
    load_all_csv_to_db()

import pandas as pd
from sqlalchemy import create_engine

# --- НАСТРОЙКИ (для твоей ЛОКАЛЬНОЙ БД) ---
DB_USER = "postgres"
DB_PASSWORD = "glavvrach228007"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "social_economics"

# Создаем папку, если ее нет
import os
if not os.path.exists('dashboard_data'):
    os.makedirs('dashboard_data')

def prepare_and_save_data():
    print("Подключаемся к локальной БД...")
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

    # --- 1. ГОТОВИМ ОСНОВНЫЕ ДАННЫЕ ---
    print("Готовим основные экономические данные...")
    sql_query = """
    SELECT region, year,
        MAX(CASE WHEN indicator_name = 'Среднедушевые денежные доходы населения' THEN indicator_value END) AS avg_income,
        MAX(CASE WHEN indicator_name = 'Уровень безработицы' THEN indicator_value END) AS unemployment_rate,
        MAX(CASE WHEN indicator_name = 'Коэффициенты миграционного прироста на 10 000 человек населения' THEN indicator_value END) AS migration_rate
    FROM (
        SELECT object_name AS region, year, indicator_name, indicator_value
        FROM rosstat_data WHERE object_level = 'регион'
    ) AS filtered_data
    GROUP BY region, year ORDER BY region, year;
    """
    main_df = pd.read_sql(sql_query, engine)
    # Сохраняем в эффективном формате Parquet
    main_df.to_parquet('dashboard_data/main_data.parquet', index=False)
    print("✅ Файл 'main_data.parquet' сохранен.")

    # --- ТУТ МОЖНО ДОБАВИТЬ ДРУГИЕ ДАННЫЕ ---
    # Например, данные для графиков с потерями, если хочешь их добавить в дашборд

    print("\nВсе данные для дашборда подготовлены!")

if __name__ == '__main__':
    prepare_and_save_data()

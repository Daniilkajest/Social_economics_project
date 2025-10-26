# ===============================================================
# КОД ИЗ prepare_data.py (ТЕПЕРЬ ОН ЗДЕСЬ)
# ===============================================================
import pandas as pd
from sqlalchemy import create_engine
import os

def prepare_and_save_data():
    # --- НАСТРОЙКИ (для твоей ЛОКАЛЬНОЙ БД) ---
    DB_USER = "postgres"
    DB_PASSWORD = "glavvrach228007" # <-- Убедись, что пароль правильный
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "social_economics"

    # Создаем папку, если ее нет
    if not os.path.exists('dashboard_data'):
        os.makedirs('dashboard_data')

    print("Подключаемся к локальной БД...")
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

    print("Готовим основные экономические данные...")
    sql_query = """
    SELECT
        region, year,
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
    main_df.to_parquet('dashboard_data/main_data.parquet', index=False)
    print("✅ Файл 'main_data.parquet' сохранен.")

# ===============================================================
# КОД ИЗ test_data_preparation.py (ТЕПЕРЬ ОН ЗДЕСЬ)
# ===============================================================
def run_test():
    """Запускает проверку скрипта подготовки данных."""
    print("\n--- Начинаем тест функции prepare_and_save_data ---")

    output_path = 'dashboard_data/main_data.parquet'

    # Запускаем нашу основную функцию
    prepare_and_save_data()

    print("\n--- Начинаем проверки ---")

    if not os.path.exists(output_path):
        print(f"❌ ПРОВАЛ: Файл {output_path} не был создан!")
        return False
    print(f"✅ ОК: Файл {output_path} успешно создан.")

    try:
        df = pd.read_parquet(output_path)
        print("✅ ОК: Parquet-файл успешно прочитан.")
    except Exception as e:
        print(f"❌ ПРОВАЛ: Не удалось прочитать Parquet-файл: {e}")
        return False

    expected_columns = ['region', 'year', 'avg_income', 'unemployment_rate', 'migration_rate']
    if not all(col in df.columns for col in expected_columns):
        print(f"❌ ПРОВАЛ: В DataFrame отсутствуют необходимые колонки.")
        return False
    print("✅ ОК: Все необходимые колонки на месте.")

    print("\n🎉🎉🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! 🎉🎉🎉")
    return True

# --- ТОЧКА ВХОДА ---
if __name__ == '__main__':
    run_test()

import pandas as pd
from prophet import Prophet
from joblib import dump
import os
from tqdm import tqdm

# --- 1. НАСТРОЙКИ ---
DATA_FILE = 'dashboard_data/main_data.parquet'
MODELS_DIR = 'models'

# --- 2. ФУНКЦИЯ ДЛЯ ОБУЧЕНИЯ МОДЕЛЕЙ ДЛЯ ОДНОГО РЕГИОНА ---
def train_and_save_model_for_region(df_region, region_name):
    """Обучает и сохраняет мультивариантную модель Prophet для одного региона."""

    df_region['ds'] = pd.to_datetime(df_region['year'], format='%Y')

    # --- Обучаем основную модель ---
    df_main = df_region[['ds', 'migration_rate', 'avg_income', 'unemployment_rate']].rename(columns={'migration_rate': 'y'})
    df_main_clean = df_main.dropna(subset=['y', 'avg_income', 'unemployment_rate'])

    if df_main_clean.shape[0] < 2:
        print(f"  ⚠️ Пропуск: Недостаточно полных данных для обучения модели для '{region_name}'.")
        return

    # Инициализируем модель с новыми, улучшенными параметрами
    model_main = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.1 # Увеличиваем гибкость тренда
    )
    model_main.add_regressor('avg_income')
    model_main.add_regressor('unemployment_rate')

    # Обучаем модель на чистых данных
    model_main.fit(df_main_clean)

    # --- Сохраняем модель ---
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    safe_filename = "".join([c for c in region_name if c.isalpha() or c.isdigit()]).rstrip()
    dump(model_main, os.path.join(MODELS_DIR, f'{safe_filename}.joblib'))
    print(f"  ✅ Модель для '{region_name}' обучена и сохранена.")

# --- 3. ГЛАВНЫЙ ЦИКЛ ОБУЧЕНИЯ ---
if __name__ == '__main__':
    print(f"Загружаем данные из {DATA_FILE}...")
    main_df = pd.read_parquet(DATA_FILE)

    all_regions = main_df['region'].unique()
    print(f"Начинаем обучение моделей для {len(all_regions)} регионов...")

    for region in tqdm(all_regions, desc="Обучение моделей"):
        # Убрали print с названием региона, чтобы progress bar был чище
        df_region_data = main_df[main_df['region'] == region]
        train_and_save_model_for_region(df_region_data, region)

    print("\n\n✅✅✅ Обучение и сохранение всех моделей завершено! ✅✅✅")
    print(f"Сохраненные модели находятся в папке: '{MODELS_DIR}'")

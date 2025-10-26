import pandas as pd
from sqlalchemy import create_engine
from tqdm import tqdm

# --- 1. ИМПОРТИРУЕМ НАШИ СОБСТВЕННЫЕ МОДУЛИ ---
# Мы импортируем функции, которые написали в других файлах
from scr.scrape_news import get_latest_headlines
from scr.sentiment_analyzer import analyze_sentiment

# --- 2. НАСТРОЙКИ ---
DB_TABLE_NAME = 'media_mentions' # Название для итоговой таблицы

# --- 3. НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БД ---
db_user = 'postgres'
db_password = 'glavvrach228007' # <-- ТВОЙ ПАРОЛЬ
db_host = 'localhost'
db_port = '5432'
db_name = 'social_economics'

def run_media_analysis_pipeline():
    """Основная функция, запускающая весь пайплайн анализа новостей."""
    try:
        # --- ШАГ 1: ПОДКЛЮЧАЕМСЯ К БД И ПОЛУЧАЕМ СПИСОК РЕГИОНОВ ---
        print("--- Шаг 1: Подключение к БД и загрузка списка регионов ---")
        engine = create_engine(f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        # Загружаем два списка: с полными названиями и с "короткими" для более гибкого поиска
        regions_df = pd.read_sql("SELECT DISTINCT region FROM casualties_regions", engine)
        region_list = regions_df['region'].tolist()
        # Создаем короткие названия, убирая "область", "край", "Республика"
        short_region_list = [r.split(' ')[0].replace('Республика', '').strip() for r in region_list]

        # Создаем словарь для обратного отображения: "Алтайский" -> "Алтайский край"
        region_mapping = {short.lower(): full for short, full in zip(short_region_list, region_list)}

        print(f"✅ Загружено {len(region_list)} регионов.")

        # --- ШАГ 2: ПАРСИМ ПОСЛЕДНИЕ НОВОСТИ ---
        print("\n--- Шаг 2: Парсинг последних новостей с РИА Новости ---")
        # Возьмем побольше новостей для анализа
        headlines_data = get_latest_headlines(limit=200)

        if not headlines_data:
            print("Не удалось получить новости. Завершение работы.")
            return

        # --- ШАГ 3: АНАЛИЗ УПОМИНАНИЙ И ТОНАЛЬНОСТИ ---
        print("\n--- Шаг 3: Поиск упоминаний регионов и анализ тональности ---")

        mentions = []
        # tqdm покажет прогресс по обработке новостей
        for news in tqdm(headlines_data, desc="Анализ новостей"):
            headline_lower = news['title'].lower()

            # Ищем упоминания коротких названий регионов в заголовке
            for short_name, full_name in region_mapping.items():
                if short_name in headline_lower and len(short_name) > 4: # Игнорируем слишком короткие названия
                    # Если нашли упоминание, анализируем тональность
                    sentiment_result = analyze_sentiment(news['title'])

                    mentions.append({
                        'region': full_name,
                        'headline': news['title'],
                        'url': news['url'],
                        'publication_time': news['time'],
                        'sentiment_label': sentiment_result['label'],
                        'sentiment_score': sentiment_result['score']
                    })
                    # Нашли один регион - переходим к следующей новости
                    break

        if not mentions:
            print("\nНе найдено ни одного упоминания регионов в последних новостях.")
            return

        print(f"\n✅ Найдено {len(mentions)} упоминаний регионов.")

        # --- ШАГ 4: ЗАГРУЗКА РЕЗУЛЬТАТОВ В БАЗУ ДАННЫХ ---
        mentions_df = pd.DataFrame(mentions)

        print(f"\n--- Шаг 4: Загрузка результатов в таблицу '{DB_TABLE_NAME}' ---")

        # Загружаем с 'replace', чтобы каждый день таблица обновлялась
        mentions_df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)

        print(f"✅ Успех! {len(mentions_df)} записей загружено в базу данных.")
        print("\n--- Пример загруженных данных ---")
        print(mentions_df.head())

    except Exception as e:
        print(f"❌ Произошла ошибка в основном пайплайне: {e}")

if __name__ == '__main__':
    run_media_analysis_pipeline()

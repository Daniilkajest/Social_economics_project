# Импортируем pipeline - самый простой способ использовать любую модель из Hugging Face
from transformers import pipeline

# --- 1. ЗАГРУЗКА МОДЕЛИ ---
# При первом запуске эта строка скачает модель (может занять несколько минут и >500 МБ)
print("Загрузка NLP-модели 'rubert-tiny2-ru-sentiment' от Hugging Face...")

# Мы используем конкретную модель, обученную на русских текстах для анализа тональности
# `pipeline` сам позаботится о загрузке и кэшировании модели
sentiment_pipeline = pipeline(
    'sentiment-analysis',
    model='MonoHime/rubert-base-cased-sentiment-new'
)

print("✅ Модель успешно загружена.")

def analyze_sentiment(text_list):
    """
    Анализирует тональность списка текстов с помощью модели из transformers.
    Возвращает список словарей с результатами.
    """
    if not isinstance(text_list, list):
        text_list = [text_list]

    # Выполняем анализ. Модель вернет список словарей.
    # Пример: [{'label': 'positive', 'score': 0.98}]
    results = sentiment_pipeline(text_list)

    if len(results) == 1:
        return results[0]
    return results

# --- 2. ТЕСТОВЫЙ ЗАПУСК ---
if __name__ == '__main__':
    test_headlines = [
        "Власти региона объявили о запуске новой социальной программы",
        "В N-ской области произошла крупная коммунальная авария",
        "Сегодня в Москве ожидается облачная погода",
        "Губернатор Ивановской области провел рабочее совещание"
    ]

    print("\n--- Тестируем анализ тональности с помощью Transformers ---")

    sentiments = analyze_sentiment(test_headlines)

    for i, headline in enumerate(test_headlines):
        sentiment = sentiments[i]
        label = sentiment['label'].upper()
        score = sentiment['score']

        print(f"\nЗаголовок: '{headline}'")
        print(f"  Результат: {label} с уверенностью {score:.2f}")

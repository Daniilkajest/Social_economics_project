import requests
import pandas as pd
from tqdm import tqdm
import time

# --- НАСТРОЙКИ ---
AREA_ID = 113 # Вся Россия

# СПИСОК ПРОФЕССИЙ, КОТОРЫЕ МЫ БУДЕМ ИСКАТЬ
PROFESSIONS_TO_SEARCH = {
    'data_analyst': 'Аналитик данных',
    'data_engineer': 'Data Engineer OR Инженер данных', # Используем OR для поиска по разным названиям
    'data_scientist': 'Data Scientist',
    'ml_engineer': 'ML Engineer OR Machine Learning',
    'nlp_engineer': 'NLP'
}

PER_PAGE = 100

def get_vacancies_by_city(text, area_id):
    """Собирает и агрегирует вакансии по городам для ОДНОГО поискового запроса."""
    base_url = 'https://api.hh.ru/vacancies'
    params = {'text': text, 'area': area_id, 'per_page': PER_PAGE, 'page': 0}

    # Первый запрос для получения метаданных
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        pages = data.get('pages', 0)
    except requests.RequestException as e:
        print(f"  ❌ Ошибка при первом запросе для '{text}': {e}")
        return None

    all_vacancies_items = []
    # tqdm будет показывать прогресс по страницам для текущей профессии
    for page in tqdm(range(pages), desc=f"  Парсинг '{text}'"):
        params['page'] = page
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            all_vacancies_items.extend(response.json().get('items', []))
            time.sleep(0.2)
        except requests.RequestException:
            # Просто пропускаем страницу, если возникла ошибка
            continue

    if not all_vacancies_items:
        return None # Возвращаем None, если ничего не найдено

    # Агрегируем данные
    cities = pd.json_normalize(all_vacancies_items)['area.name']
    city_counts = cities.value_counts().reset_index()
    city_counts.columns = ['city', 'vacancies_count']
    return city_counts

if __name__ == '__main__':
    print("🚀 Начинаем сбор данных о вакансиях с HeadHunter...")

    # Создаем DataFrame, с которым будем объединять результаты
    final_df = None

    # Основной цикл по словарю профессий
    for key, search_query in PROFESSIONS_TO_SEARCH.items():
        print(f"\n[--- Ищем профессию: {search_query} ---]")

        # Получаем DataFrame с количеством вакансий по городам для текущей профессии
        vacancies_df = get_vacancies_by_city(search_query, AREA_ID)

        if vacancies_df is not None:
            # Переименовываем колонку 'vacancies_count' в соответствии с ключом профессии
            vacancies_df = vacancies_df.rename(columns={'vacancies_count': key})

            # Объединяем результаты
            if final_df is None:
                final_df = vacancies_df
            else:
                # Используем 'outer' join, чтобы не потерять города,
                # которые есть в одном датафрейме, но нет в другом.
                final_df = pd.merge(final_df, vacancies_df, on='city', how='outer')

            print(f"  ✅ Найдено и обработано. Топ-3 города: \n{vacancies_df.head(3)}")
        else:
            print(f"  ⚠️ Для '{search_query}' вакансий не найдено или произошла ошибка.")

    if final_df is not None:
        # Заполняем пропуски (NaN) нулями, так как если город не нашелся, значит там 0 вакансий
        final_df = final_df.fillna(0)

        # Преобразуем числовые колонки в целые числа
        for col in PROFESSIONS_TO_SEARCH.keys():
            if col in final_df.columns:
                final_df[col] = final_df[col].astype(int)

        print("\n\n--- Итоговая таблица (первые 15 строк) ---")
        print(final_df.head(15))

        # Сохраняем итоговый, объединенный файл
        output_filename = 'hh_vacancies_by_city.csv'
        final_df.to_csv(output_filename, index=False, encoding='utf-8')
        print(f"\n✅ Все результаты успешно сохранены в один файл: '{output_filename}'")
    else:
        print("\nНе удалось собрать никаких данных.")

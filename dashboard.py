
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px  # <-- ВАЖНЫЙ ИМПОРТ

# --- 1. НАСТРОЙКИ СТРАНИЦЫ И ПОДКЛЮЧЕНИЕ ---
st.set_page_config(page_title="Анализ регионов РФ", layout="wide")
st.title("Интерактивный дашборд: Социально-экономический анализ регионов РФ")

# Подключаемся к Supabase, как в видео
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(supabase_url, supabase_key)
    st.success("✅ Успешно подключились к Supabase API!")
except Exception as e:
    st.error("❌ Не удалось подключиться к Supabase. Проверьте секреты SUPABASE_URL и SUPABASE_KEY.")
    st.exception(e)
    st.stop() # Останавливаем выполнение, если нет подключения

# --- 2. ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data_from_supabase():
    # Загружаем данные из таблицы rosstat_data.
    # API Supabase может иметь лимит (например, 1000 строк).
    # Чтобы получить все, нужно делать запросы в цикле.
    print("Загрузка данных из Supabase...")
    all_data = []
    offset = 0
    limit = 1000
    while True:
        response = supabase.table('rosstat_data').select("*").range(offset, offset + limit - 1).execute()
        data = response.data
        if not data:
            break
        all_data.extend(data)
        offset += limit

    if not all_data:
        st.warning("Не удалось загрузить данные из таблицы 'rosstat_data'.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data)

    # Фильтруем нужные показатели прямо здесь
    indicators_to_keep = [
        'Среднедушевые денежные доходы населения', 'Уровень безработицы',
        'Коэффициенты миграционного прироста на 10 000 человек населения'
    ]
    df = df[df['indicator_name'].isin(indicators_to_keep)]

    # Трансформация данных
    wide_df = df.pivot_table(index=['region', 'year'], columns='indicator_name', values='indicator_value').reset_index()
    wide_df.columns.name = None

    # --- ВАЖНО: ПЕРЕИМЕНОВАНИЕ КОЛОНОК ---
    wide_df = wide_df.rename(columns={
        'Среднедушевые денежные доходы населения': 'avg_income',
        'Уровень безработицы': 'unemployment_rate',
        'Коэффициенты миграционного прироста на 10 000 человек населения': 'migration_rate'
    })
    # ------------------------------------
    return wide_df

main_df = load_data_from_supabase()

# --- 3. ИНТЕРФЕЙС ДАШБОРДА ---
if main_df.empty:
    st.warning("Не удалось загрузить данные для отображения.")
else:
    st.sidebar.header("Фильтры")
    selected_regions = st.sidebar.multiselect(
        "Выберите регионы:",
        options=sorted(main_df['region'].unique()),
        default=['Москва', 'Республика Тыва', 'Тюменская область']
    )

    indicator_options = {
        'Среднедушевой доход': 'avg_income',
        'Уровень безработицы': 'unemployment_rate',
        'Миграционный прирост': 'migration_rate'
    }
    selected_indicator_name = st.sidebar.selectbox(
        "Выберите показатель:",
        options=list(indicator_options.keys())
    )
    selected_indicator_col = indicator_options[selected_indicator_name]

    if not selected_regions:
        st.warning("Пожалуйста, выберите хотя бы один регион.")
    else:
        df_filtered = main_df[main_df['region'].isin(selected_regions)]
        st.header(f"Динамика показателя: '{selected_indicator_name}'")
        fig = px.line(df_filtered, x='year', y=selected_indicator_col, color='region', title=f"Динамика '{selected_indicator_name}'", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.header("Анализ корреляций")
        col1, col2 = st.columns(2)
        x_axis_name = col1.selectbox("Ось X:", options=list(indicator_options.keys()), index=0)
        y_axis_name = col2.selectbox("Ось Y:", options=list(indicator_options.keys()), index=2)
        x_axis_col = indicator_options[x_axis_name]
        y_axis_col = indicator_options[y_axis_name]

        # Убедимся, что last_year существует
        if not main_df.empty:
            last_year = main_df['year'].max()
            df_corr = main_df[main_df['year'] == last_year]
            fig2 = px.scatter(df_corr, x=x_axis_col, y=y_axis_col, hover_name='region', size=x_axis_col, color='region', title=f"Связь '{x_axis_name}' и '{y_axis_name}' в {last_year} г.", trendline='ols')
            st.plotly_chart(fig2, use_container_width=True)

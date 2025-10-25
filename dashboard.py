import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# --- 1. НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Анализ регионов РФ", layout="wide")
st.title("Интерактивный дашборд: Социально-экономический анализ регионов РФ")

# --- 2. ПОДКЛЮЧЕНИЕ К БД И ЗАГРУЗКА ДАННЫХ ---
# Этот блок будет выполнен один раз и закэширован
@st.cache_data
def load_and_prepare_data():
    # --- Подключение ---
    try:
        db_url = (
        f"postgresql://{st.secrets.postgres.user}:{st.secrets.postgres.password}@"
        f"{st.secrets.postgres.host}:{st.secrets.postgres.port}/{st.secrets.postgres.dbname}"
    )
        engine = create_engine(db_url)

        with engine.connect() as connection:
            st.success("✅ Успех! Соединение с БД установлено (прямое подключение).")

    except Exception as e:
    st.error("❌ Этап 1: Ошибка создания движка (прямое подключение).")
    st.exception(e)
    return pd.DataFrame()

    # --- SQL-запрос ---
    sql_query = """
    SELECT
        object_name AS region, year, indicator_name, indicator_value
    FROM rosstat_data
    WHERE object_level = 'регион'
      AND indicator_name IN (
        'Среднедушевые денежные доходы населения', 'Уровень безработицы',
        'Коэффициенты миграционного прироста на 10 000 человек населения'
      )
    """

    # --- Выполнение запроса ---
    try:
        df = pd.read_sql(sql_query, engine)
        if df.empty:
            st.warning("⚠️ Этап 2: SQL-запрос выполнен, но не вернул данных.")
            return pd.DataFrame()
    except Exception as e:
        st.error("❌ Этап 2: Ошибка при выполнении SQL-запроса.")
        st.exception(e)
        return pd.DataFrame()

    # --- Трансформация ---
    try:
        wide_df = df.pivot_table(index=['region', 'year'], columns='indicator_name', values='indicator_value').reset_index()
        wide_df.columns.name = None
        wide_df = wide_df.rename(columns={
            'Среднедушевые денежные доходы населения': 'avg_income',
            'Уровень безработицы': 'unemployment_rate',
            'Коэффициенты миграционного прироста на 10 000 человек населения': 'migration_rate'
        })
        return wide_df
    except Exception as e:
        st.error("❌ Этап 3: Ошибка при трансформации данных (pivot_table).")
        st.exception(e)
        return pd.DataFrame()

# --- 3. ЗАПУСК ЗАГРУЗКИ И ПРОВЕРКА ---
main_df = load_and_prepare_data()

if main_df.empty:
    st.error("Не удалось загрузить или обработать данные. Дальнейшее выполнение невозможно. Проверьте ошибки выше.")
else:
    # --- 4. ИНТЕРФЕЙС ДАШБОРДА (только если данные загружены) ---
    st.sidebar.header("Фильтры")
    selected_regions = st.sidebar.multiselect(
        "Выберите регионы:",
        options=sorted(main_df['region'].unique()),
        default=['Москва', 'Республика Тыва']
    )

    # ... (остальной код для графиков остается таким же, как был)
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
        last_year = main_df['year'].max()
        df_corr = main_df[main_df['year'] == last_year]
        fig2 = px.scatter(df_corr, x=x_axis_col, y=y_axis_col, hover_name='region', size=x_axis_col, color='region', title=f"Связь '{x_axis_name}' и '{y_axis_name}' в {last_year} г.", trendline='ols')
        st.plotly_chart(fig2, use_container_width=True)

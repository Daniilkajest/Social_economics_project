import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px # Будем использовать Plotly для красивых интерактивных графиков

# --- НАСТРОЙКИ СТРАНИЦЫ ---
# Устанавливаем заголовок и иконку для вкладки в браузере. Должно быть первой командой.
st.set_page_config(page_title="Анализ регионов РФ", layout="wide")

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ---
# Эта функция будет кэшироваться, чтобы не подключаться к БД каждый раз при изменении виджета
@st.cache_resource
def get_db_engine():
    db_user = 'postgres'
    db_password = 'glavvrach228007' # <-- ТВОЙ ПАРОЛЬ
    db_host = 'localhost'
    db_port = '5432'
    db_name = 'social_economics'
    try:
        engine = create_engine(f'postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
        print("DB Connection Success")
        return engine
    except Exception as e:
        print(f"DB Connection Failed: {e}")
        st.error("Не удалось подключиться к базе данных. Проверьте настройки и пароль.")
        return None

engine = get_db_engine()

# --- ЗАГРУЗКА ДАННЫХ ---
# Эта функция тоже кэшируется, чтобы не выполнять тяжелые SQL-запросы постоянно
@st.cache_data
def load_data(_engine):
    if _engine is None:
        return pd.DataFrame()

    # Загружаем нашу "широкую" таблицу с основными показателями
    # Мы можем сделать это одним SQL-запросом, как мы делали в Jupyter
    sql_query = """
    SELECT
        object_name AS region, year, indicator_name, indicator_value
    FROM rosstat_data
    WHERE object_level = 'регион'
      AND indicator_name IN (
        'Среднедушевые денежные доходы населения', 'Уровень безработицы',
        'Коэффициенты миграционного прироста на 10 000 человек населения',
        'Общие коэффициенты рождаемости', 'Общие коэффициенты смертности'
      )
    """
    df = pd.read_sql(sql_query, _engine)

    # Трансформируем данные
    wide_df = df.pivot_table(index=['region', 'year'], columns='indicator_name', values='indicator_value').reset_index()
    wide_df.columns.name = None

    # Переименовываем колонки для удобства
    wide_df = wide_df.rename(columns={
        'Среднедушевые денежные доходы населения': 'avg_income',
        'Уровень безработицы': 'unemployment_rate',
        'Коэффициенты миграционного прироста на 10 000 человек населения': 'migration_rate',
        'Общие коэффициенты рождаемости': 'birth_rate',
        'Общие коэффициенты смертности': 'death_rate'
    })

    return wide_df

# Загружаем данные при старте приложения
main_df = load_data(engine)

# --- ИНТЕРФЕЙС ДАШБОРДА ---

st.title("Интерактивный дашборд: Социально-экономический анализ регионов РФ")

# --- Боковая панель с фильтрами ---
st.sidebar.header("Фильтры")

# Выбор региона (мультиселект)
selected_regions = st.sidebar.multiselect(
    "Выберите регионы для сравнения:",
    options=sorted(main_df['region'].unique()),
    default=['Москва', 'Республика Тыва', 'Чеченская Республика'] # Регионы по умолчанию
)

# Выбор показателя для отображения
indicator_options = {
    'Среднедушевой доход': 'avg_income',
    'Уровень безработицы': 'unemployment_rate',
    'Миграционный прирост': 'migration_rate'
}
selected_indicator_name = st.sidebar.selectbox(
    "Выберите показатель для анализа:",
    options=list(indicator_options.keys())
)
selected_indicator_col = indicator_options[selected_indicator_name]

# --- ОСНОВНАЯ ЧАСТЬ: ГРАФИКИ ---

if not selected_regions:
    st.warning("Пожалуйста, выберите хотя бы один регион в панели слева.")
else:
    # Фильтруем DataFrame по выбранным регионам
    df_filtered = main_df[main_df['region'].isin(selected_regions)]

    st.header(f"Динамика показателя: '{selected_indicator_name}'")

    # Строим интерактивный линейный график с помощью Plotly Express
    fig = px.line(
        df_filtered,
        x='year',
        y=selected_indicator_col,
        color='region', # Разные цвета для разных регионов
        title=f"Динамика показателя '{selected_indicator_name}' по годам",
        markers=True # Добавляем точки на график
    )
    fig.update_layout(xaxis_title="Год", yaxis_title=selected_indicator_name)
    st.plotly_chart(fig, use_container_width=True) # Отображаем график

    # --- Второй график: Связь двух показателей ---
    st.header("Анализ корреляций")

    # Выбор показателей для осей X и Y
    col1, col2 = st.columns(2)
    with col1:
        x_axis_name = st.selectbox("Показатель для оси X:", options=list(indicator_options.keys()), index=0)
    with col2:
        y_axis_name = st.selectbox("Показатель для оси Y:", options=list(indicator_options.keys()), index=2)

    x_axis_col = indicator_options[x_axis_name]
    y_axis_col = indicator_options[y_axis_name]

    # Данные за последний год
    last_year = main_df['year'].max()
    df_corr = main_df[main_df['year'] == last_year]

    fig2 = px.scatter(
        df_corr,
        x=x_axis_col,
        y=y_axis_col,
        hover_name='region', # При наведении будет показываться название региона
        size=x_axis_col,     # Размер точки зависит от показателя X
        color='region',      # Раскрашиваем по регионам
        title=f"Связь '{x_axis_name}' и '{y_axis_name}' в {last_year} г.",
        trendline='ols'      # Добавляем линию тренда!
    )
    fig2.update_layout(xaxis_title=x_axis_name, yaxis_title=y_axis_name)
    st.plotly_chart(fig2, use_container_width=True)

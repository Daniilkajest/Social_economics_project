import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. НАСТРОЙКИ СТРАНИЦЫ ---
# Эта команда должна быть первой
st.set_page_config(
    page_title="Анализ регионов РФ",
    page_icon="🇷🇺",
    layout="wide"
)

st.title("Интерактивный дашборд: Социально-экономический анализ регионов РФ")

# --- 2. ЗАГРУЗКА ДАННЫХ ИЗ ФАЙЛА ---
# Streamlit будет кэшировать эти данные для быстрой работы
@st.cache_data
def load_data():
    """Загружает подготовленные данные из локального файла Parquet."""
    try:
        # Дашборд ожидает, что рядом с ним есть папка 'dashboard_data' с файлом внутри
        df = pd.read_parquet('dashboard_data/main_data.parquet')
        return df
    except FileNotFoundError:
        st.error(
            "❌ Файл 'dashboard_data/main_data.parquet' не найден! "
            "Пожалуйста, сначала запустите локально скрипт `prepare_data.py`, "
            "чтобы сгенерировать этот файл, и убедитесь, что он загружен на GitHub."
        )
        return pd.DataFrame()

# Загружаем данные
main_df = load_data()

# --- 3. ОСНОВНАЯ ЛОГИКА И ИНТЕРФЕЙС ---
# Весь последующий код будет выполняться, только если данные были успешно загружены
if not main_df.empty:

    # --- Боковая панель с фильтрами ---
    st.sidebar.header("Фильтры")

    # Мультиселект для выбора регионов
    all_regions = sorted(main_df['region'].unique())
    selected_regions = st.sidebar.multiselect(
        "Выберите регионы для сравнения:",
        options=all_regions,
        default=['Москва', 'Республика Тыва', 'Тюменская область', 'Краснодарский край']
    )

    # Словарь для выбора показателя
    indicator_options = {
        'Среднедушевой доход': 'avg_income',
        'Уровень безработицы': 'unemployment_rate',
        'Миграционный прирост': 'migration_rate'
    }

    # --- Раздел 1: Динамика по годам ---
    st.header("Динамика показателей по годам")

    selected_indicator_name = st.selectbox(
        "Выберите показатель для анализа динамики:",
        options=list(indicator_options.keys())
    )
    selected_indicator_col = indicator_options[selected_indicator_name]

    if not selected_regions:
        st.warning("Пожалуйста, выберите хотя бы один регион в панели слева.")
    else:
        # Фильтруем DataFrame по выбранным регионам
        df_filtered = main_df[main_df['region'].isin(selected_regions)]

        # Строим интерактивный линейный график
        fig_line = px.line(
            df_filtered,
            x='year',
            y=selected_indicator_col,
            color='region',
            title=f"Динамика показателя '{selected_indicator_name}'",
            markers=True,
            labels={'year': 'Год', selected_indicator_col: selected_indicator_name}
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- Раздел 2: Анализ корреляций ---
    st.header("Анализ связей между показателями")

    last_year = main_df['year'].max()
    selected_year = st.slider(
        "Выберите год для анализа корреляций:",
        min_value=int(main_df['year'].min()),
        max_value=int(last_year),
        value=int(last_year)
    )

    col1, col2 = st.columns(2)
    with col1:
        x_axis_name = st.selectbox("Показатель для оси X:", options=list(indicator_options.keys()), index=0)
    with col2:
        y_axis_name = st.selectbox("Показатель для оси Y:", options=list(indicator_options.keys()), index=2)

    x_axis_col = indicator_options[x_axis_name]
    y_axis_col = indicator_options[y_axis_name]

    # --- ГЛАВНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ ---
    # Фильтруем данные И СРАЗУ удаляем строки, где в нужных нам колонках есть пропуски
    df_corr = main_df[main_df['year'] == selected_year].dropna(subset=[x_axis_col, y_axis_col])
    # --------------------------------

# Проверяем, остались ли данные после очистки
    if df_corr.empty:
        st.warning(f"Нет полных данных для построения графика '{x_axis_name}' vs '{y_axis_name}' за {selected_year} год.")
    else:
        fig_scatter = px.scatter(
            df_corr,
            x=x_axis_col,
            y=y_axis_col,
            hover_name='region',
            size=x_axis_col,
            color='region',
            title=f"Связь '{x_axis_name}' и '{y_axis_name}' в {selected_year} г.",
            trendline='ols',
            labels={x_axis_col: x_axis_name, y_axis_col: y_axis_name},
            color_discrete_map={region: 'rgba(0,0,0,0)' for region in df_corr['region'].unique()}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- Отображение таблицы с данными ---
    with st.expander("Показать таблицу с данными"):
        st.dataframe(main_df)

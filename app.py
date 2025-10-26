import streamlit as st
import pandas as pd
import plotly.express as px
from prophet import Prophet
from joblib import load
import os
import numpy as np # <-- ВОТ ВАЖНЫЙ ИМПОРТ

# --- 1. НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Анализ регионов РФ",
    page_icon="🇷🇺",
    layout="wide"
)

# --- 2. ФУНКЦИИ ЗАГРУЗКИ ---
@st.cache_data
def load_data():
    try:
        df = pd.read_parquet('dashboard_data/main_data.parquet')
        return df
    except FileNotFoundError:
        st.error("❌ Файл 'dashboard_data/main_data.parquet' не найден!")
        return pd.DataFrame()

@st.cache_resource
def load_model(region_name):
    try:
        safe_filename = "".join([c for c in region_name if c.isalpha() or c.isdigit()]).rstrip()
        model_path = os.path.join('models', f'{safe_filename}.joblib')
        model = load(model_path)
        return model
    except FileNotFoundError:
        st.warning(f"⚠️ Модель для региона '{region_name}' не найдена.")
        return None

# --- ЗАГРУЗКА ДАННЫХ ---
main_df = load_data()

# --- 3. НАВИГАЦИЯ ---
st.sidebar.title("Навигация")
page = st.sidebar.radio("Выберите раздел", ["Анализ данных", "Прогнозирование ML"])

# ==============================================================================
# --- СТРАНИЦА 1: АНАЛИЗ ДАННЫХ ---
# ==============================================================================
if page == "Анализ данных":
    st.title("Интерактивный дашборд: Социально-экономический анализ регионов РФ")

    if not main_df.empty:
        st.sidebar.header("Фильтры")
        all_regions = sorted(main_df['region'].unique())
        selected_regions = st.sidebar.multiselect(
            "Выберите регионы для сравнения:",
            options=all_regions,
            default=['Москва', 'Республика Тыва', 'Тюменская область', 'Краснодарский край']
        )

        indicator_options = {
            'Среднедушевой доход': 'avg_income',
            'Уровень безработицы': 'unemployment_rate',
            'Миграционный прирост': 'migration_rate'
        }

        st.header("Динамика показателей по годам")
        selected_indicator_name = st.selectbox(
            "Выберите показатель для анализа динамики:",
            options=list(indicator_options.keys())
        )
        selected_indicator_col = indicator_options[selected_indicator_name]

        if not selected_regions:
            st.warning("Пожалуйста, выберите хотя бы один регион.")
        else:
            df_filtered = main_df[main_df['region'].isin(selected_regions)]
            fig_line = px.line(
                df_filtered, x='year', y=selected_indicator_col, color='region',
                title=f"Динамика показателя '{selected_indicator_name}'", markers=True,
                labels={'year': 'Год', selected_indicator_col: selected_indicator_name}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.header("Анализ связей между показателями")
        last_year_available = int(main_df['year'].max())
        first_year_available = int(main_df['year'].min())
        selected_year = st.slider(
            "Выберите год:",
            min_value=first_year_available, max_value=last_year_available, value=last_year_available
        )

        col1, col2 = st.columns(2)
        x_axis_name = col1.selectbox("Показатель для оси X:", options=list(indicator_options.keys()), index=0)
        y_axis_name = col2.selectbox("Показатель для оси Y:", options=list(indicator_options.keys()), index=2)

        x_axis_col = indicator_options[x_axis_name]
        y_axis_col = indicator_options[y_axis_name]

        if x_axis_col == y_axis_col:
            st.warning("Пожалуйста, выберите разные показатели.")
        else:
            df_corr = main_df[main_df['year'] == selected_year].dropna(subset=[x_axis_col, y_axis_col])
            if df_corr.empty:
                st.warning(f"Нет полных данных для '{x_axis_name}' vs '{y_axis_name}' за {selected_year} г.")
            else:
                size_data = df_corr[x_axis_col] - df_corr[x_axis_col].min() + 1
                fig_scatter = px.scatter(
                    df_corr, x=x_axis_col, y=y_axis_col, hover_name='region',
                    size=size_data, color='region',
                    title=f"Связь '{x_axis_name}' и '{y_axis_name}' в {selected_year} г.",
                    trendline='ols', labels={x_axis_col: x_axis_name, y_axis_col: y_axis_name}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

        with st.expander("Показать таблицу с данными"):
            st.dataframe(main_df)

# ==============================================================================
# --- СТРАНИЦА 2: ПРОГНОЗИРОВАНИЕ ML ---
# ==============================================================================
elif page == "Прогнозирование ML":
    st.title("Прогнозирование миграционного прироста с помощью ML")

    if not main_df.empty:
        st.sidebar.header("Настройки прогноза")
        all_regions = sorted(main_df['region'].unique())

        region_to_forecast = st.sidebar.selectbox(
            "Выберите регион для прогноза:",
            options=all_regions,
            index=all_regions.index('Москва') if 'Москва' in all_regions else 0
        )

        forecast_horizon = st.sidebar.slider("Горизонт прогноза (лет):", 1, 5, 3)

        st.header(f"Прогноз для региона: {region_to_forecast}")

        model = load_model(region_to_forecast)

        if model:
            with st.spinner('Строим прогноз...'):
                df_region = main_df[main_df['region'] == region_to_forecast].copy()
                df_region['ds'] = pd.to_datetime(df_region['year'], format='%Y')

                def get_future_values(df, col, periods):
                    df_temp = df[['ds', col]].rename(columns={col: 'y'}).dropna()
                    if len(df_temp) < 2: return None
                    m = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
                    m.fit(df_temp)
                    future = m.make_future_dataframe(periods=periods, freq='A')
                    return m.predict(future)[['ds', 'yhat']].rename(columns={'yhat': col})

                future_income = get_future_values(df_region, 'avg_income', forecast_horizon)
                future_unemployment = get_future_values(df_region, 'unemployment_rate', forecast_horizon)

                if future_income is not None and future_unemployment is not None:
                    future_df = model.make_future_dataframe(periods=forecast_horizon, freq='A')
                    historical_regressors = df_region[['ds', 'avg_income', 'unemployment_rate']]
                    future_df = pd.merge(future_df, historical_regressors, on='ds', how='left')
                    future_df = future_df.set_index('ds')
                    future_df.update(future_income.set_index('ds'))
                    future_df.update(future_unemployment.set_index('ds'))
                    future_df = future_df.reset_index()
                    future_df = future_df.fillna(method='ffill').fillna(method='bfill')

                    forecast = model.predict(future_df)

                    st.subheader("График прогноза")
                    fig = model.plot(forecast, xlabel='Год', ylabel='Миграционный прирост')
                    st.pyplot(fig)

                    st.subheader("Компоненты прогноза")
                    fig_components = model.plot_components(forecast)
                    st.pyplot(fig_components)

                    st.subheader("Данные прогноза")
                    st.dataframe(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_horizon))
                else:
                    st.error("Не удалось построить прогноз для регрессоров.")

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

st.set_page_config(page_title="LLM Data Analyst", layout="wide")
st.title("🧠 Мини-продукт: LLM-аналитика данных")
st.caption("OpenRouter + Прямой API вызов")

# Отключение прокси
for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(var, None)

uploaded_file = st.file_uploader("Загрузите CSV-файл для анализа", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 Предпросмотр данных")
        st.dataframe(df.head(10), use_container_width=True)

    with col2:
        st.metric("Строк", len(df))
        st.metric("Колонок", len(df.columns))

    openrouter_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        help="Получить можно на https://openrouter.ai/keys"
    )

    model_name = st.selectbox(
        "Выберите модель",
        options=[
            "openrouter/free",
            "google/gemini-2.5-flash",
            "openai/gpt-4o-mini",
            "mistralai/mistral-7b-instruct",
            "qwen/qwen2.5-7b-instruct",
        ],
        index=0
    )

    analysis_type = st.radio(
        "Тип анализа",
        ["Полный автоматический анализ", "Свободный запрос к данным"]
    )

    if openrouter_key and st.button("🚀 Запустить анализ", type="primary"):
        with st.spinner("Нейросеть анализирует данные..."):
            try:
                data_sample = df.head(20).to_string(index=False)
                columns_info = "\n".join([f"- {col} ({df[col].dtype})" for col in df.columns])

                if analysis_type == "Полный автоматический анализ":
                    prompt = f"""Ты — профессиональный аналитик данных.

Датасет содержит следующие колонки:
{columns_info}

Пример первых 20 строк данных:
{data_sample}

Проведи полный анализ на русском языке и верни **только** JSON без лишнего текста:

{{
  "summary": "Краткое описание датасета (1-2 предложения)",
  "key_metrics": {{"колонка1": "статистика", "колонка2": "статистика"}},
  "main_insights": ["инсайт 1", "инсайт 2", "инсайт 3"],
  "correlations": "основные взаимосвязи",
  "potential_problems": ["возможные проблемы"],
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}}
"""
                else:
                    user_query = st.text_input("Введи свой вопрос:",
                                               placeholder="Какой средний возраст? Сколько продаж в каждом регионе?")
                    prompt = f"""Датасет:
Колонки:
{columns_info}

Пример данных:
{data_sample}

Вопрос: {user_query}

Ответь подробно и профессионально на русском языке."""

                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1500
                }

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=100
                )

                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    st.subheader("📝 Результат анализа")

                    try:
                        parsed = json.loads(content)
                        st.json(parsed)
                    except:
                        st.markdown(content)
                else:
                    st.error(f"Ошибка API: {response.status_code}\n{response.text}")

            except Exception as e:
                st.error(f"Произошла ошибка: {e}")

else:
    st.info("👆 Загрузите CSV-файл, чтобы начать анализ")
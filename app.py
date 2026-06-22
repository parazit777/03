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
st.caption("Анализ всего датасета + осмысленные графики")

for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(var, None)

uploaded_file = st.file_uploader("Загрузите CSV-файл", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.success(f"✅ Загружено **{len(df)} строк** и **{len(df.columns)} колонок**")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 Предпросмотр")
        st.dataframe(df.head(15), use_container_width=True)

    with col2:
        st.metric("Строк", len(df))
        st.metric("Колонок", len(df.columns))
        st.metric("Пропущенных значений", df.isnull().sum().sum())

    openrouter_key = st.text_input("OpenRouter API Key", type="password",
                                   help="https://openrouter.ai/keys")

    model_name = st.selectbox("Модель",
                              options=["google/gemini-2.5-flash", "openai/gpt-4o-mini", "openrouter/free"],
                              index=0)

    if openrouter_key and st.button("🚀 Запустить профессиональный анализ", type="primary"):
        with st.spinner("LLM проводит полный анализ датасета..."):
            try:
                # Полная информация о датасете
                prompt = f"""Ты — профессиональный data analyst с 10-летним опытом.
Проанализируй этот датасет полностью ({len(df)} строк, {len(df.columns)} колонок).

Колонки: {list(df.columns)}
Типы данных: {df.dtypes.to_dict()}
Пропуски: {df.isnull().sum().to_dict()}
Основная статистика:
{df.describe(include='all').round(4).to_string()}

Сделай **глубокий** анализ и верни **только** JSON:

{{
  "summary": "Общее описание датасета и бизнес-контекст",
  "key_insights": ["5 самых важных инсайтов"],
  "data_quality": "Оценка качества данных",
  "business_recommendations": ["3-5 практических рекомендаций"],
  "plots": [
    {{"title": "Название графика", "code": "plotly.express код, который можно выполнить"}}
  ]
}}"""

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 2500
                    },
                    timeout=150
                )

                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    result = json.loads(content)

                    st.subheader("📝 Итоговый анализ")
                    st.markdown(result.get("summary", ""))

                    st.subheader("🔑 Ключевые инсайты")
                    for insight in result.get("key_insights", []):
                        st.write(f"• {insight}")

                    st.subheader("💼 Бизнес-рекомендации")
                    for rec in result.get("business_recommendations", []):
                        st.write(f"• {rec}")

                    # Графики
                    st.subheader("📈 Графики от LLM")
                    for plot in result.get("plots", []):
                        st.write(f"**{plot.get('title')}**")
                        try:
                            exec(plot["code"])
                        except Exception as e:
                            st.error(f"Не удалось построить график: {e}")
                else:
                    st.error(f"Ошибка API: {response.status_code}")

            except Exception as e:
                st.error(f"Ошибка: {e}")

else:
    st.info("Загрузите CSV-файл для анализа")

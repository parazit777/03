import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

st.set_page_config(page_title="LLM Data Analyst", layout="wide")
st.title("🧠 Мини-продукт: LLM-аналитика данных")
st.caption("Полный анализ датасета + осмысленные графики")

# Отключение прокси
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

    openrouter_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        help="https://openrouter.ai/keys"
    )

    model_name = st.selectbox(
        "Модель",
        options=["google/gemini-2.5-flash", "openai/gpt-4o-mini", "openrouter/free"],
        index=0
    )

    if openrouter_key and st.button("🚀 Запустить профессиональный анализ", type="primary"):
        with st.spinner("LLM анализирует датасет..."):
            try:
                prompt = f"""Ты — senior data analyst.
Проанализируй датасет ({len(df)} строк, {len(df.columns)} колонок).

Колонки: {list(df.columns)}
Пропуски: {df.isnull().sum().to_dict()}
Статистика:
{df.describe(include='all').round(4).to_string()}

Верни **только** JSON:

{{
  "summary": "описание датасета",
  "key_insights": ["инсайт 1", "инсайт 2"],
  "business_recommendations": ["рекомендация 1"],
  "plots": [
    {{"title": "Название графика", "code": "код plotly.express без import"}}
  ]
}}"""

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.25,
                        "max_tokens": 2500
                    },
                    timeout=150
                )

                content = response.json()["choices"][0]["message"]["content"]

                # Парсинг JSON
                try:
                    result = json.loads(content)
                except:
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    result = json.loads(json_match.group(0)) if json_match else {"summary": content}

                # Вывод
                st.subheader("📝 Анализ")
                st.markdown(result.get("summary", ""))

                st.subheader("🔑 Ключевые инсайты")
                for insight in result.get("key_insights", []):
                    st.write("•", insight)

                st.subheader("💼 Рекомендации")
                for rec in result.get("business_recommendations", []):
                    st.write("•", rec)

                # Графики
                st.subheader("📈 Графики от LLM")
                for plot in result.get("plots", []):
                    st.write(f"**{plot.get('title')}**")
                    try:
                        code = plot["code"]
                        # Убираем import, если они есть
                        code = re.sub(r'^\s*import .*?px.*?$', '', code, flags=re.MULTILINE)
                        code = re.sub(r'^\s*from plotly.*?$', '', code, flags=re.MULTILINE)

                        local_vars = {"df": df, "px": px, "st": st}
                        exec(code, {"__builtins__": {}}, local_vars)
                    except Exception as e:
                        st.error(f"Ошибка графика: {e}")

            except Exception as e:
                st.error(f"Ошибка: {e}")

else:
    st.info("👆 Загрузите CSV-файл для анализа")

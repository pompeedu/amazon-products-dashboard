
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

# ---------------------------------------------
# НАСТРОЙКИ СТРАНИЦЫ И ФУТЕРА
# ---------------------------------------------
st.set_page_config(
    page_icon = ":tangerine:",
    page_title ="Дашборд товаров Amazon",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные цвета
st.markdown("""
<style>
    a {color: #FF732C !important;}
    a:hover {color: #FFFFFF !important;}
    [data-testid="stMetricValue"] {color: #FF732C !important;}
    [data-testid="stAlert"] div:first-child {color: #FFFFFF !important;
                                             background-color: #2D1208 !important;}
    [class="st-emotion-cache-9rsxm2 et2rgd20"] {font-size: 1.2rem !important;}
    
    [data-testid="stSidebarContent"] {
        position: relative;
        height: 100vh;        
    }        
            
    
    .footer {
        z-index: 9999;
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        color: gray;
        line-height: 1.2;
        text-align: center;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(6px);
        }
    .sidebar-caption {
        position: fixed;
        bottom: 0px;
        left: 14px;
        width: calc(var(--sidebar-width, 22rem) - 10px);
        z-index: 99999;

        line-height: 1;
        font-size: 12px;
        color: #9CA3AF;
        text-align: center;
        
    }

    div[data-testid="stSidebarUserContent"] {
        padding-bottom: 110px;
    }
            
</style>    

<div class="footer">
<p><b>Telegram:  </b><a href='https://t.me/pompeedu' target='_blank'>@pompeedu</a></p>
<p><b>Email:  </b><a href='mailto:firuzjonkurbonov735700@gmail.com' target='_blank'>firuzjonkurbonov735700@gmail.com</a>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------
# ЗАГОЛОВОК И ОПИСАНИЕ
# ---------------------------------------------
st.title("📦 Дашборд товаров Amazon")
st.markdown("""
##### Чистый и удобный дашборд для анализа товаров Amazon: цен, рейтингов и обзоров.  
""")

# ---------------------------------------------
# ЗАГРУЗКА ДАННЫХ
# ---------------------------------------------
@st.cache_data(show_spinner="Загрузка данных...")
def load_data(file):
    return pd.read_csv(file)

df = load_data("Amazon.csv")
if load_data is None:
    st.toast("Нет данных.", icon="👆")
    st.stop()

# ---------------------------------------------
# ОЧИСТКА ДАННЫХ
# ---------------------------------------------
@st.cache_data(show_spinner="Чистим данные...")
def clean_numeric(value):
    if pd.isna(value):
        return np.nan
    value = str(value)
    value = (
        value.replace(",", "")
        .replace("$", "")
        .replace("₹", "")
        .replace("%", "")
        .replace("£", "")
        .replace("€", "")
        .replace("¥", "")
        .replace("₽", "")
        .replace("руб", "")
        .replace("-", "")
        .strip()
    )
    if value == "":
        return np.nan
    try:
        return float(value)
    except:
        return np.nan

numeric_columns = ["discounted_price", "actual_price", "discount_percentage", "rating", "rating_count"]
for col in numeric_columns:
    df[col] = df[col].apply(clean_numeric)

df[numeric_columns] = df[numeric_columns].fillna(0)
df.drop_duplicates(inplace=True)

# ---------------------------------------------
# ФИЛЬТРЫ В САЙДБАРЕ
# ---------------------------------------------
st.sidebar.markdown("# 🎛 Фильтры")
st.sidebar.markdown("---")
# Слайдер цены
min_price = int(df["discounted_price"].min())
max_price = int(df["discounted_price"].max())
price_range = st.sidebar.slider("Диапазон цены", min_value=min_price, max_value=max_price, value=(min_price, max_price))

# Слайдер рейтинга
rating_range = st.sidebar.slider(
    "Диапазон рейтинга",
    min_value=float(df["rating"].min()),
    max_value=float(df["rating"].max()),
    value=(0.0, 5.0)
)
st.sidebar.markdown("---")
# MULTISELECT по категориям
all_categories = sorted(df["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Категории",
    options=["Все"] + all_categories,
    default=["Все"]
)

st.sidebar.markdown("""
<div class="sidebar-caption">                                                                              
    <p>Разработано как демонстрационный проект для портфолио</p>
    <p>Готов создать аналогичное решение для вашего бизнеса</p>
</div>                    
""", unsafe_allow_html=True)
# ---------------------------------------------
# ПРИМЕНЕНИЕ ФИЛЬТРОВ
# ---------------------------------------------
df_filtered = df.copy()
if "Все" not in selected_categories:
    df_filtered = df_filtered[df_filtered["category"].isin(selected_categories)]

df_filtered = df_filtered[
    (df_filtered["discounted_price"] >= price_range[0]) &
    (df_filtered["discounted_price"] <= price_range[1]) &
    (df_filtered["rating"] >= rating_range[0]) &
    (df_filtered["rating"] <= rating_range[1])
]

# ---------------------------------------------
# СОКРАЩЁННОЕ НАЗВАНИЕ КАТЕГОРИИ
# ---------------------------------------------
df_filtered['category_short'] = df_filtered['category'].apply(lambda x: x.split("|")[-1])

# ---------------------------------------------
# МЕТРИКИ
# ---------------------------------------------
st.markdown("---")
st.subheader("🎯 Метрики")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Количество товаров", len(df_filtered), border=True)
with col2:
    st.metric("Средний рейтинг", round(df_filtered["rating"].mean(), 2), border=True)
with col3:
    st.metric("Средняя скидка, %", round(df_filtered["discount_percentage"].mean(), 2), border=True)
with col4:
    st.metric("Средняя цена", round(df_filtered["discounted_price"].mean(), 2), border=True)

st.markdown("---")

# ---------------------------------------------
# ТОП ТОВАРОВ
# ---------------------------------------------
st.subheader("🔥 Топ-товары")

top_products = df_filtered.sort_values("rating_count", ascending=False).head(5)
cols = st.columns(5)
placeholder_img = "https://dummyimage.com/300x300/cccccc/000000&text=No+Image"

@st.cache_data(show_spinner="Загрузка...")
def is_image_available(url: str) -> bool:
    if not isinstance(url, str) or not url.startswith("http"):
        return False
    try:
        response = requests.head(url, timeout=3)
        return response.status_code == 200
    except:
        return False

for col, (_, row) in zip(cols, top_products.iterrows()):
    with col:
        img_url = row.get("img_link", "")
        if is_image_available(img_url):
            st.image(img_url, width="stretch")
        else:
            st.image(placeholder_img, width="stretch")
        st.markdown(f"**{row['product_name'][:40]}...**")
        st.markdown(f"⭐ {row['rating']} &nbsp;&nbsp; 💬 {row['rating_count']}")
        st.markdown(f"[Открыть товар]({row['product_link']})")
st.markdown("---")

# ---------------------------------------------
# ВИЗУАЛИЗАЦИИ
# ---------------------------------------------
st.subheader("📊 Визуализации")

# Топ категорий по выручке
revenue_by_category = df_filtered.groupby("category_short")["discounted_price"].sum().reset_index()
top_revenue = revenue_by_category.sort_values("discounted_price", ascending=False).head(5)
fig_revenue = px.bar(
    top_revenue,
    x="category_short",
    y="discounted_price",
    text="discounted_price",
    title="Топ категорий по выручке",
    hover_data={"category_short": False}
)
fig_revenue.update_traces(marker_color='#FF732C', textposition='auto', opacity=0.8)
fig_revenue.update_layout(font=dict(color='white'), xaxis=dict(gridcolor='#444'), yaxis=dict(gridcolor='#444'))
st.plotly_chart(fig_revenue, use_container_width=True, config={"responsive": True})

# Распределение рейтингов
fig_rating = px.histogram(df_filtered, x="rating", nbins=20, title="Распределение рейтингов")
fig_rating.update_layout(font=dict(color='white'), xaxis=dict(gridcolor='#444'), yaxis=dict(gridcolor='#444'))
fig_rating.update_traces(marker=dict(color='#FF732C', opacity=0.8))
st.plotly_chart(fig_rating, use_container_width=True, config={"responsive": True})

# Средняя скидка по категориям
discount_by_category = df_filtered.groupby("category_short")["discount_percentage"].mean().reset_index()
fig_disc = px.bar(discount_by_category, x="category_short", y="discount_percentage",
                  title="Средняя скидка по категориям", hover_data={"category_short": False})
fig_disc.update_traces(marker=dict(color='#FF732C', opacity=0.8))
fig_disc.update_layout(font=dict(color='white'), xaxis=dict(gridcolor='#444'), yaxis=dict(gridcolor='#444'))
st.plotly_chart(fig_disc, use_container_width=True, config={"responsive": True})

# Диаграмма "Цена vs Рейтинг"
fig_corr = px.scatter(df_filtered, x="discounted_price", y="rating",
                      size="rating_count", hover_name="product_name", opacity=0.8,
                      title="Цена vs рейтинг")
fig_corr.update_layout(font=dict(color='white'), xaxis=dict(gridcolor='#444'), yaxis=dict(gridcolor='#444'))
fig_corr.update_traces(marker=dict(color='#FF732C', opacity=0.8, size=10))
st.plotly_chart(fig_corr, use_container_width=True, config={"responsive": True})

# Матрица корреляции
numeric_cols = ["discounted_price", "actual_price", "discount_percentage", "rating", "rating_count"]
corr_matrix = df_filtered[numeric_cols].corr()
fig_corr_matrix = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='Viridis',
                            title="Матрица корреляции")
fig_corr_matrix.update_layout(font=dict(color='white'), width=900, height=900)
st.plotly_chart(fig_corr_matrix, use_container_width=True, config={"responsive": True})

st.markdown("---")

# ---------------------------------------------
# КЛЮЧЕВЫЕ ВЫВОДЫ
# ---------------------------------------------
st.subheader("💡 Ключевые выводы")

avg_rating_by_cat = df_filtered.groupby("category")["rating"].mean().reset_index()
top_rating_cat = avg_rating_by_cat.loc[avg_rating_by_cat["rating"].idxmax()]

avg_discount_by_cat = df_filtered.groupby("category")["discount_percentage"].mean().reset_index()
top_discount_cat = avg_discount_by_cat.loc[avg_discount_by_cat["discount_percentage"].idxmax()]

avg_price_by_cat = df_filtered.groupby("category")["discounted_price"].mean().reset_index()
top_price_cat = avg_price_by_cat.loc[avg_price_by_cat["discounted_price"].idxmax()]

def last_category(cat):
    return cat.split("|")[-1]


col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"## 📌 Категория **{last_category(top_rating_cat['category'])}** лидирует по среднему рейтингу")
    st.metric(
        "",
        f"{top_rating_cat['rating']:.2f}",
        label_visibility="hidden"
    )
with col2:
    st.markdown(f"## 📌 **{last_category(top_discount_cat['category'])}** имеет наибольшие скидки")
    st.metric(
        "",
        f"{top_discount_cat['discount_percentage']:.0f}%",
        label_visibility="hidden"
    )
with col3:
    st.markdown(f"## 📌 **{last_category(top_price_cat['category'])}** — самая дорогая категория")
    st.metric(
        "",
        f"{top_price_cat['discounted_price']:.2f}",
        label_visibility="hidden"
    )
st.markdown('###')

st.info('''
Совет: сфокусируйтесь на категориях, которые уже показывают сильные метрики:
- улучшение карточек товаров
- расширение ассортимента
- аккуратное тестирование цен

в топ-категориях это даёт самый быстрый прирост продаж.
''', icon="💬")

st.markdown("---")

# ---------------------------------------------
# ТАБЛИЦА ДАННЫХ
# ---------------------------------------------
st.subheader("📄 Отфильтрованные данные")
st.dataframe(df_filtered, width="stretch")
st.download_button("Скачать отфильтрованные данные", df_filtered.to_csv(index=False), "filtered_Amazon.csv")

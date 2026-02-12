import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import os
import random
from urllib.parse import quote

# ================= 1. 初始化與檔案處理 =================
DB_FILE = "movie_modern_storage.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 確保 Session State 初始化
if "my_list" not in st.session_state:
    st.session_state.my_list = load_data()
if "popular_cache" not in st.session_state:
    st.session_state.popular_cache = []

# ================= 2. 爬蟲工具箱 =================

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }

def fetch_imdb_trending():
    """抓取 IMDb 熱門排行榜"""
    url = "https://www.imdb.com/chart/moviemeter/"
    movies = []
    try:
        res = requests.get(url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select('li.ipc-metadata-list-summary-item')
        for item in items[:12]:
            title_tag = item.select_one('h3.ipc-title__text')
            img_tag = item.select_one('img.ipc-image')
            if title_tag and img_tag:
                title = title_tag.get_text().split('. ', 1)[-1]
                movies.append({
                    "title": title,
                    "poster": img_tag.get('src'),
                    "watched": False
                })
    except Exception as e:
        st.error(f"排行榜更新失敗: {e}")
    return movies

def auto_find_poster(name):
    """自動尋找海報"""
    search_url = f"https://www.imdb.com/find?q={quote(name)}&s=tt&ttype=ft"
    try:
        res = requests.get(search_url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        img = soup.select_one('.ipc-metadata-list-summary-item img')
        return img.get('src') if img else "https://via.placeholder.com/200x300?text=No+Poster"
    except:
        return "https://via.placeholder.com/200x300?text=Search+Error"

# ================= 3. 介面設計 =================

st.set_page_config(page_title="電影管家", page_icon="🍿", layout="wide")

# 套用乾淨的現代 CSS
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; font-weight: 600; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍿 電影口袋名單")

tab1, tab2 = st.tabs(["🔥 發現熱門", "📁 我的片單管理"])

# --- Tab 1: 發現熱門 ---
with tab1:
    if st.button("🔄 更新 IMDb 熱門電影"):
        with st.spinner("正在連線至 IMDb..."):
            st.session_state.popular_cache = fetch_imdb_trending()
    
    if st.session_state.popular_cache:
        st.write("---")
        cols = st.columns(4)
        for idx, movie in enumerate(st.session_state.popular_cache):
            with cols[idx % 4]:
                st.image(movie['poster'], width='stretch')
                st.write(f"**{movie['title']}**")
                if st.button("➕ 加入清單", key=f"pop_{idx}"):
                    if movie['title'] not in [m['title'] for m in st.session_state.my_list]:
                        st.session_state.my_list.append(movie.copy())
                        save_data(st.session_state.my_list)
                        st.success(f"已加入 {movie['title']}")
                    else:
                        st.warning("已在清單中")

# --- Tab 2: 片單管理 ---
with tab2:
    # 側邊欄：手動新增
    with st.sidebar:
        st.header("✍️ 快速新增")
        m_name = st.text_input("輸入電影名稱")
        if st.button("自動找圖並加入"):
            if m_name:
                with st.spinner("正在尋找海報..."):
                    p_url = auto_find_poster(m_name)
                    st.session_state.my_list.append({"title": m_name, "poster": p_url, "watched": False})
                    save_data(st.session_state.my_list)
                    st.rerun()

    if not st.session_state.my_list:
        st.info("清單空空的。")
    else:
        to_watch = [m for m in st.session_state.my_list if not m.get('watched', False)]
        watched = [m for m in st.session_state.my_list if m.get('watched', False)]

        col_main, col_side = st.columns([2, 1])

        with col_main:
            st.subheader(f"⏳ 想看的電影 ({len(to_watch)})")
            for i, movie in enumerate(st.session_state.my_list):
                if not movie.get('watched', False):
                    with st.container():
                        c1, c2, c3 = st.columns([1, 3, 1])
                        c1.image(movie['poster'], width=100)
                        c2.markdown(f"### {movie['title']}")
                        with c3:
                            if st.button("✅ 已看", key=f"done_{i}"):
                                movie['watched'] = True
                                save_data(st.session_state.my_list)
                                st.rerun()
                            if st.button("🗑️ 刪除", key=f"del_{i}"):
                                st.session_state.my_list.pop(i)
                                save_data(st.session_state.my_list)
                                st.rerun()

        with col_side:
            st.subheader("🎲 抽籤")
            if to_watch:
                if st.button("🎰 隨機選一部"):
                    pick = random.choice(to_watch)
                    st.balloons()
                    st.image(pick['poster'], width='stretch')
                    st.success(f"就決定是：{pick['title']}")
            
            st.write("---")
            if watched:
                with st.expander("✅ 已觀看紀錄"):
                    for i, movie in enumerate(st.session_state.my_list):
                        if movie.get('watched', False):
                            cx, cy = st.columns([4, 1])
                            cx.write(f"~~{movie['title']}~~")
                            if cy.button("🔙", key=f"un_{i}"):
                                movie['watched'] = False
                                save_data(st.session_state.my_list)
                                st.rerun()

    if st.session_state.my_list:
        if st.button("🔥 一鍵清除所有資料"):
            st.session_state.my_list = []
            save_data([])
            st.rerun()
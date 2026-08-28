import streamlit as st
import json
import os
from supabase import create_client, Client

# --- 設定 ---
# ここにSupabaseの情報を正しく貼り付けてください！
SUPABASE_URL = "https://ozlqdcyfnzvvmflynsgt.supabase.co" 
SUPABASE_KEY = "sb_publishable_UeVmmGVGTZE2Za0a8sGIQw_Wnc15XtW"

# Supabaseクライアントの初期化
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabaseへの接続に失敗しました。URLとAPIキーを再確認してください。: {e}")
    st.stop()

# --- データの読み込み（ローカルの補助用） ---
CONFIG_FILE = "config.json"

def load_config():
    default_config = {
        "categories": ["家電", "IT・ツール", "株・投資", "その他"],
        "history": {}
    }
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            for key in default_config:
                if key not in loaded_config:
                    loaded_config[key] = default_config[key]
            return loaded_config
    else:
        return default_config

config = load_config()

# --- 画面の構成 ---
st.set_page_config(page_title="自分専用・知識ベース", layout="centered")

st.title("📚 知識ベース")
st.write("身の回りの取説や、学んだことをストックする場所です。")

# --- サイドバー：新規登録 ---
with st.sidebar:
    st.header("⚙️ 新規登録")
    new_title = st.text_input("タイトル")
    new_cat = st.selectbox("カテゴリ", config["categories"])
    new_desc = st.text_area("説明")
    new_how = st.text_area("使い方")
    new_term = st.text_area("用語")
    new_set = st.text_input("設定")
    
    if st.button("保存する", type="primary"):
        if new_title:
            try:
                # Supabaseへデータを挿入
                response = supabase.table("entries").insert({
                    "title": new_title,
                    "category": new_cat,
                    "description": new_desc,
                    "how_to_use": new_how,
                    "terminology": new_term,
                    "settings": new_set
                }).execute()
                
                if response.data:
                    st.success("Supabaseに保存しました！")
                    st.rerun()
            except Exception as e:
                st.error(f"保存中にエラーが発生しました: {e}")
        else:
            st.warning("タイトルを入力してください")
            
    st.write("---")
    st.header("🔍 検索")
    search_query = st.text_input("キーワードで検索")

# --- メインコンテンツ ---
# データ取得（Supabaseから最新を取得）
try:
    # 検索条件の整理
    query = supabase.table("entries").select("*")
    if search_query:
        # タイトルまたは内容にキーワードが含まれるものを取得
        query = query.ilike("title", f"%{search_query}%").or_("description", f"%{search_query}%")
    
    response = query.execute()
    entries = response.data
except Exception as e:
    st.error(f"データの取得に失敗しました: {e}")
    entries = []

# 表示の切り替え
if "view_id" in st.session_state:
    # 詳細表示画面
    entry = next((e for e in entries if e["id"] == st.session_state.view_id), None)
    if entry:
        if st.button("← 一覧に戻る"):
            st.session_state.view_id = None
            st.rerun()
        
        st.markdown(f"## {entry['title']}")
        st.caption(f"カテゴリ: {entry['category']}")
        st.write("---")
        
        st.markdown("### 📝 説明")
        st.write(entry["description"])
        
        st.markdown("### 🛠 使い方")
        st.write(entry["how_to_use"])
        
        st.markdown("### 📖 用語")
        st.write(entry["terminology"])
        
        st.markdown("### ⚙️ 設定")
        st.write(entry["settings"])
    else:
        st.warning("データが見つかりません。")
else:
    # 一覧表示画面
    if not entries:
        st.info("登録されている知識がありません。サイドバーから追加してください。")
    else:
        for entry in entries:
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: #f0f2f6;
                    padding: 20px;
                    border-radius: 15px;
                    margin-bottom: 15px;
                    border: 1px solid #ddd;
                ">
                    <p style="font-size: 20px; font-weight: bold; margin: 0; color: #333;">{entry['title']}</p>
                    <p style="font-size: 16px; color: #666; margin: 5px 0;">{entry['category']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"詳細を見る", key=f"btn_{entry['id']}"):
                    st.session_state.view_id = entry["id"]
                    st.rerun()

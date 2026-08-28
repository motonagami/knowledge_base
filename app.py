import streamlit as st
import json
import os
from supabase import create_client, Client

# --- 設定 ---
# あなたの情報をここに貼り付けてください
SUPABASE_URL = "ozlqdcyfnzvvmflynsgt"  # あなたのProject URL
SUPABASE_KEY = "sb.publishable_UevmmGYTZEZ...（ここにコピーしたAPIキーを貼る）" # あなたのAPIキー

# Supabaseクライアントの初期化
# ※APIキーが正しい場合のみ動作します
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabaseへの接続に失敗しました。URLとAPIキーが正しいか確認してください。: {e}")

# --- データの読み書き関数 ---
# データの「バックアップ」としてローカルのJSONも保持する仕組みにします
CONFIG_FILE = "knowledge_base.json"

def load_local_config():
    default_config = {
        "categories": ["家電", "IT・ツール", "株・投資", "その他"],
        "history": {}
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_config

def save_local_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

config = load_config()

# --- 画面の構成 ---
st.set_page_config(page_title="自分専用・知識ベース", layout="centered")

st.title("📚 知識ベース")
st.write("Supabaseと連携した、消えない知識ベースです。")

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
            # Supabaseへデータを挿入
            try:
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

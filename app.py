import streamlit as st
import json
import os
from datetime import datetime

# --- 設定と初期化 ---
# フォルダのパスを動的に取得します
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "knowledge_base.json")

def load_config():
    default_config = {
        "entries": [],
        "categories": ["家電", "IT・ツール", "株・投資", "その他"]
    }
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            # 足りない項目があれば補う
            for key in default_config:
                if key not in loaded_config:
                    loaded_config[key] = default_config[key]
            return loaded_config
    else:
        return default_config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

config = load_config()

# --- 画面の構成 ---
st.set_page_config(page_title="自分専用・知識ベース", layout="centered")

# --- ヘッダー ---
st.title("📚 知識ベース")
st.write("身の回りの取説や、学んだことをストックする場所です。")

# --- サイドバー：新規登録と検索 ---
with st.sidebar:
    st.header("⚙️ 新規登録")
    new_title = st.text_input("タイトル")
    new_cat = st.selectbox("カテゴリ", config["categories"])
    new_desc = st.text_area("説明", placeholder="概要を書いてください")
    new_how = st.text_area("使い方", placeholder="手順などを書いてください")
    new_term = st.text_area("用語", placeholder="専門用語の解説")
    new_set = st.text_input("設定", placeholder="パスや注意点など")
    
    if st.button("保存する", type="primary"):
        if new_title:
            new_entry = {
                "id": str(datetime.now().timestamp()),
                "title": new_title,
                "category": new_cat,
                "description": new_desc,
                "how_to_use": new_how,
                "terminology": new_term,
                "settings": new_set,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            config["entries"].append(new_entry)
            save_config(config)
            st.success("保存しました！")
            st.rerun()
        else:
            st.warning("タイトルを入力してください")
            
    st.write("---")
    st.header("🔍 検索")
    search_query = st.text_input("キーワードで検索")

# --- メインコンテンツ ---
# 検索とカテゴリフィルタの適用
filtered_entries = []
if search_query:
    filtered_entries = [
        e for e in config["entries"] 
        if search_query in e["title"] or search_query in e["description"] or search_query in e["how_to_use"]
    ]
else:
    filtered_entries = config["entries"]

# カテゴリ選択の反映（検索と組み合わせる）
# 今回は簡易的に検索優先とし、検索がない場合のみカテゴリを考慮する形にします
# もし特定のカテゴリを絞り込みたい場合はここにロジックを追加します

# 表示の切り替え
if "view_id" in st.session_state:
    # 詳細表示画面
    entry = next((e for e in filtered_entries if e["id"] == st.session_state.view_id), None)
    if entry:
        if st.button("← 一覧に戻る"):
            st.session_state.view_id = None
            st.rerun()
        
        st.markdown(f"## {entry['title']}")
        st.caption(f"カテゴリ: {entry['category']} | 登録日: {entry['date']}")
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
    if not filtered_entries:
        st.info("登録されている知識がありません。サイドバーから追加してください。")
    else:
        for entry in filtered_entries:
            with st.container():
                # カード風の表示
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
                # クリックで詳細を見るためのボタン（擬似的な挙動）
                if st.button(f"詳細を見る", key=f"btn_{entry['id']}"):
                    st.session_state.view_id = entry["id"]
                    st.rerun()

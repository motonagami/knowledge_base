import streamlit as st
import json
import os
import io
import pdfplumber
import google.generativeai as genai
from supabase import create_client, Client

# --- 設定 ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("エラー: 設定（Secrets）が見つかりません。Streamlitの管理画面から設定してください。")
    st.stop()

# Geminiの初期設定
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"AIの初期化に失敗しました: {e}")

# Supabaseクライアントの初期化
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabaseへの接続に失敗しました。URLとAPIキーを再確認してください。: {e}")
    st.stop()

# --- データの読み込み ---
CONFIG_FILE = "config.json"
def load_config():
    default_config = {"categories": ["家電", "IT・ツール", "株・投資", "その他"], "history": {}}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            for key in default_config:
                if key not in loaded_config: loaded_config[key] = default_config[key]
            return loaded_config
    return default_config

config = load_config()

# --- 関数定義 ---
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text: full_text += text + "\n"
            return full_text
    except Exception as e:
        st.error(f"PDF処理中にエラーが発生しました: {e}")
        return None

def generate_ai_summary(raw_text):
    prompt = f"""
    以下のテキストは、家電の取扱説明書や技術資料から抽出されたものです。
    この内容を元に、以下の4つの項目に分けて日本語でわかりやすく要約してください。
    項目：
    1. 📝 説明（概要を短く）
    2. 🛠 使い方（重要な操作手順を箇条書きで）
    3. 📖 用語（重要な言葉の解説）
    4. ⚙️ 設定（注意点や設定のコツ）
    テキスト：
    {raw_text}
    出力形式（JSON形式で返してください）:
    {{
        "description": "...",
        "how_to_use": "...",
        "terminology": "...",
        "settings": "..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        content = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"AIによる要約中にエラーが発生しました: {e}")
        return None

# --- 画面の構成 ---
st.set_page_config(page_title="自分専用・知識ベース", layout="wide")

st.title("📚 知識ベース")
st.write("身の回りの取説や、学んだことをストックする場所です。")

# --- サイドバー ---
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
                response = supabase.table("entries").insert({
                    "title": new_title, "category": new_cat, "description": new_desc,
                    "how_to_use": new_how, "terminology": new_term, "settings": new_set
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
    
    st.write("---")
    st.header("📄 PDFからAI要約")
    uploaded_file = st.file_uploader("PDFファイルを選択...", type=["pdf"])
    if uploaded_file is not None:
        if st.button("AIで要約を作成"):
            with st.spinner("PDFを読み取り、AIが要約を作成中..."):
                raw_text = extract_text_from_pdf(uploaded_file)
                if raw_text:
                    if len(raw_text.strip()) < 10:
                        st.warning("PDFから有効なテキストが読み取れませんでした。")
                    else:
                        summary = generate_ai_summary(raw_text)
                        if summary:
                            st.session_state["ai_draft"] = {
                                "title": new_title if new_title else "（未入力）",
                                "category": new_cat,
                                "description": summary.get("description", ""),
                                "how_to_use": summary.get("how_to_use", ""),
                                "terminology": summary.get("terminology", ""),
                                "settings": summary.get("settings", "")
                            }
                            st.success("AIによる下書きが完成しました！")
                            st.rerun()
                else:
                    st.warning("PDFを読み取れませんでした。")

# --- データの取得 ---
try:
    # データベースから全件取得
    response = supabase.table("entries").select("*").execute()
    all_entries = response.data or []
except Exception as e:
    st.error(f"データの取得に失敗しました: {e}")
    all_entries = []

# --- 表示の切り替えロジック ---
if "view_id" in st.session_state and st.session_state.view_id is not None:
    # 詳細表示画面
    entry = next((e for e in all_entries if e["id"] == st.session_state.view_id), None)
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

elif "ai_draft" in st.session_state:
    draft = st.session_state["ai_draft"]
    st.header("🤖 AIが作った下書き")
    st.info("内容を確認し、必要であれば修正してから「保存する」を押してください。")
    st.markdown("---")
    final_title = st.text_input("タイトル", value=draft["title"])
    final_cat = st.selectbox("カテゴリ", config["categories"], index=config["categories"].index(draft["category"]) if draft["category"] in config["categories"] else 0)
    final_desc = st.text_area("説明", value=draft["description"], height=150)
    final_how = st.text_area("使い方", value=draft["how_to_use"], height=150)
    final_term = st.text_area("用語", value=draft["terminology"], height=100)
    final_set = st.text_input("設定", value=draft["settings"])
    
    if st.button("この内容で保存する", type="primary", use_container_width=True):
        try:
            response = supabase.table("entries").insert({
                "title": final_title, "category": final_cat, "description": final_desc,
                "how_to_use": final_how, "terminology": final_term, "settings": final_set
            }).execute()
            if response.data:
                st.success("保存しました！")
                del st.session_state["ai_draft"]
                st.rerun()
        except Exception as e:
            st.error(f"保存中にエラーが発生しました: {e}")

else:
    # 一覧表示画面（ここを修正しました）
    if search_query:
        # 検索窓に文字が入っているときは、そのキーワードでフィルタリング
        entries = [
            e for e in all_entries 
            if search_query.lower() in e["title"].lower() 
            or search_query.lower() in e["description"].lower()
            or search_query.lower() in e["how_to_use"].lower()
            or search_query.lower() in e["terminology"].lower()
        ]
    else:
        # 検索窓が空のときは、すべてのデータを表示
        entries = all_entries

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

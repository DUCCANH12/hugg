import streamlit as st
import requests
import json
import re
import time
import streamlit.components.v1 as components # Thêm thư viện này

# Cấu hình cơ bản
st.set_page_config(page_title="Shopee Tool", layout="centered")

# --- PHẦN CSS CỦA BẠN (GIỮ NGUYÊN VÀ TỐI ƯU THÊM) ---
st.markdown("""
    <style>
        div[data-testid="stExpander"] { display: none !important; }
        button[id="tabs-bui3-tab-1"] { display: none !important; }
        div[data-baseweb="tab-list"] { display: none !important; }
        .st-emotion-cache-1y4p8pa { padding: 1rem 1rem 5rem !important; }
        .st-emotion-cache-18ni7ap { display: none !important; }
        h1 { text-align: center !important; font-size: 24px !important; color: #EE4D2D; padding-top: 0px !important;}
        .st-emotion-cache-1avcm0n { display: none !important; }
        footer { visibility: hidden; }
        .stCodeBlock { border-radius: 10px !important; }
        .
    </style>
""", unsafe_allow_html=True)

# --- HÀM TẠO NÚT COPY TRỰC QUAN ---
def ntn_copy_button(content):
    # Escape nội dung để tránh lỗi JavaScript
    safe_content = json.dumps(content)
    custom_button = f"""
    <div id="copy-container" style="margin-top: 10px;">
        <button id="copy-btn" onclick="copyFunc()" style="
            width: 100%;
            padding: 14px;
            background: linear-gradient(90deg, #ff8a00, #EE4D2D);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-family: sans-serif;
            box-shadow: 0 4px 15px rgba(238, 77, 45, 0.3);
        ">📋 Copy!</button>
    </div>

    <script>
    function copyFunc() {{
        const text = {safe_content};
        navigator.clipboard.writeText(text).then(() => {{
            const btn = document.getElementById('copy-btn');
            btn.innerHTML = '✅ Đã Copy!';
            btn.style.background = '#28a745';
            setTimeout(() => {{
                btn.innerHTML = '📋 Copy!';
                btn.style.background = 'linear-gradient(90deg, #ff8a00, #EE4D2D)';
            }}, 2000);
        }});
    }}
    </script>
    """
    components.html(custom_button, height=80)

# ===== HÀM XỬ LÝ COOKIE & API (GIỮ NGUYÊN) =====
def process_cookie_input(raw_input):
    if not raw_input: return ""
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict) and "cookies" in data:
            return "; ".join([f"{c['name']}={c['value']}" for c in data["cookies"] if "name" in c])
        return raw_input
    except: return raw_input

if "SHOPEE_COOKIE" in st.secrets:
    cookie_str = process_cookie_input(st.secrets["SHOPEE_COOKIE"])
else:
    st.error("Chưa cấu hình SHOPEE_COOKIE!")
    st.stop()

def call_api(links, sub_dict):
    url = "https://affiliate.shopee.vn/api/v3/gql?q=batchCustomLink"
    headers = {
        "content-type": "application/json",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
    }
    payload = {
        "operationName": "batchGetCustomLink",
        "query": "query batchGetCustomLink($linkParams: [CustomLinkParam!], $sourceCaller: SourceCaller) { batchCustomLink(linkParams: $linkParams, sourceCaller: $sourceCaller) { shortLink, failCode } }",
        "variables": {"linkParams": [{"originalLink": l, "advancedLinkParams": sub_dict} for l in links], "sourceCaller": "CUSTOM_LINK_CALLER"}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        return r.json().get('data', {}).get('batchCustomLink', [])
    except: return []

# ===== GIAO DIỆN CHÍNH =====
st.title("Chuyển Đổi Link")

with st.expander("⚙️ Cấu hình SubID"):
    sub_ids = {}
    c1, c2 = st.columns(2)
    for i in range(1, 5):
        target = c1 if i % 2 != 0 else c2
        val = target.text_input(f"SubID {i}", key=f"s{i}")
        if val: sub_ids[f"subId{i}"] = val

tab1, tab2 = st.tabs(["📋 Link List", "📝 Content"])

with tab1:
    txt = st.text_area("Nhập link (mỗi dòng 1 link):", height=150, placeholder="Dán link Shopee vào đây...")
    if st.button("🚀 Chuyển đổi", use_container_width=True):
        links = [l.strip() for l in txt.split('\n') if l.strip()]
        if links:
            with st.spinner('Đang lấy link...'):
                res = call_api(links, sub_ids)
                out = [r.get('shortLink') or f"Lỗi {r.get('failCode')}" for r in res]
                final_result = "\n".join(out)
                st.code(final_result)
                ntn_copy_button(final_result) # Chèn nút copy mới

with tab2:
    con = st.text_area("Dán bài viết cần thay link:", height=200)
    if st.button("🔄 Thay thế link", use_container_width=True):
        found = list(set(re.findall(r'(https?://s\.shopee\.vn/[a-zA-Z0-9]+)', con)))
        if found:
            with st.spinner('Đang thay thế...'):
                res = call_api(found, sub_ids)
                new_con = con
                for old, r in zip(found, res):
                    if r.get('shortLink'): 
                        new_con = new_con.replace(old, r['shortLink'])
                st.code(new_con)
                ntn_copy_button(new_con) # Chèn nút copy mới

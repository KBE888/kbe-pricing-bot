import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# ==========================================
# 0. 核心初始化 (绝对防弹)
# ==========================================
st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_lang", "中文")
st.session_state.setdefault("chat_session", None)

# ==========================================
# 1. 核心配置
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！请配置 Cloud Secrets。")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE ❄️ 智能客服", page_icon="❄️", layout="centered")

# ==========================================
# 2. 首页顶部渲染 (Logo 与 语言选择)
# ==========================================
# 用两列布局，把 Logo 和语言切换并排放在首页最顶部
top_col1, top_col2 = st.columns([1, 1])

with top_col1:
    st.image(LOGO_URL, width=150)

with top_col2:
    # 🎯 关键修改：把语言选择放在首页右上方，而不是侧边栏
    selected_lang = st.segmented_control(
        "Language / 语言", 
        ["中文", "English"], 
        default=st.session_state.current_lang,
        key="lang_selector"
    )
    
    if selected_lang and selected_lang != st.session_state.current_lang:
        st.session_state.current_lang = selected_lang
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

st.markdown(f"<h2 style='color:{BRAND_COLOR}; margin-top:-10px;'>智能客服与报价助手</h2>" if st.session_state.current_lang == "中文" else f"<h2 style='color:{BRAND_COLOR}; margin-top:-10px;'>AI Service & Quote</h2>", unsafe_allow_html=True)

# ==========================================
# 3. 首页快捷联系按钮 (手机用户最爱)
# ==========================================
st.markdown("---")
btn_col1, btn_col2, btn_col3 = st.columns(3)
with btn_col1:
    st.markdown(f"[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/6588972601)")
with btn_col2:
    st.markdown(f"[![Call](https://img.shields.io/badge/Call_Us-0078D4?style=for-the-badge&logo=phone&logoColor=white)](tel:65067330)")
with btn_col3:
    st.markdown(f"[![Website](https://img.shields.io/badge/Website-Global-gray?style=for-the-badge)](https://www.kbe.com.sg/)")

# ==========================================
# 4. 系统指令
# ==========================================
lang = st.session_state.current_lang
system_instruction = f"""
你现在是 KBE 公司的冷气专家。语言：{lang}。回复要简短（2-3句）。
1. 视觉诊断：分析图片给原因，引导预约。
2. 报价：普通洗$49起，药水洗$130起。先问细节再报价。
3. 预约：引导点击 WhatsApp 链接 https://wa.me/6588972601。
"""

# ==========================================
# 5. 初始化 AI 模型
# ==========================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 6. 聊天功能与图片上传
# ==========================================
# 图片上传放在首页，方便手机拍照
upload_label = "📸 上传冷气故障照片" if lang == "中文" else "📸 Upload issue photo"
uploaded_file = st.file_uploader(upload_label, type=["jpg", "jpeg", "png"])

if len(st.session_state.messages) == 0:
    welcome = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断冷气故障。" if lang == "中文" else "Hello! I am KBE expert. I can provide quotes or diagnose issues via photos."
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

if prompt := st.chat_input("描述您的问题..." if lang == "中文" else "Describe your issue..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant", avatar="❄️"):
        msg_ph = st.empty()
        # 同时处理文字和图片
        content = [prompt]
        if uploaded_file:
            img = Image.open(uploaded_file)
            content.append(img)
            st.toast("图片分析中..." if lang == "中文" else "Analyzing image...")

        response = st.session_state.chat_session.send_message(content)
        msg_ph.markdown(response.text)
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})

# ==========================================
# 7. 底部社交媒体链接 (放在首页最下面)
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 14px;">
    <a href="https://www.facebook.com/kbeaircon/">Facebook</a> | 
    <a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | 
    <a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | 
    <a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">小红书</a>
</div>
""", unsafe_allow_html=True)

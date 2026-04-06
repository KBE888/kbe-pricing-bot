import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# ==========================================
# 0. 核心初始化
# ==========================================
st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_lang", "中文")
st.session_state.setdefault("chat_session", None)

# ==========================================
# 1. 配置与样式
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE AI", page_icon="❄️", layout="centered")

# 强制隐藏原生上传进度条并优化布局
st.markdown(f"""
<style>
    .stChatInput {{ margin-top: -20px; }}
    .stFileUploaderSection {{ padding: 0 !important; }}
    [data-testid="stBaseButton-secondary"] {{ border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 首页顶部 (Logo & 语言)
# ==========================================
c1, c2 = st.columns([1, 1])
with c1:
    st.image(LOGO_URL, width=130)
with c2:
    selected_lang = st.segmented_control(
        "Lang", ["中文", "English"], 
        default=st.session_state.current_lang, key="lang_selector", label_visibility="collapsed"
    )
    if selected_lang and selected_lang != st.session_state.current_lang:
        st.session_state.current_lang = selected_lang
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

lang = st.session_state.current_lang
if lang == "中文":
    welcome = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断故障。"
    hint = "描述问题..."
    disclaimer = "\n\n> 💡 **温馨提示**：AI 图片分析结果仅供参考，实际请以师傅上门检查为准。"
    wa_text, call_text, web_text = "WhatsApp", "拨打电话", "官方网站"
else:
    welcome = "Hello! I am KBE expert. I can provide quotes or diagnose issues via photos."
    hint = "Describe issue..."
    disclaimer = "\n\n> 💡 **Note**: AI diagnosis is for reference only. On-site inspection is recommended."
    wa_text, call_text, web_text = "WhatsApp", "Call Us", "Website"

# ==========================================
# 3. 首页三金刚按钮 (并排显示)
# ==========================================
st.markdown("---")
b1, b2, b3 = st.columns(3)
b1.link_button(f"🟢 {wa_text}", "https://wa.me/6588972601", use_container_width=True)
b2.link_button(f"🔵 {call_text}", "tel:65067330", use_container_width=True)
b3.link_button(f"⚪ {web_text}", "https://www.kbe.com.sg/", use_container_width=True)

# ==========================================
# 4. 模型初始化
# ==========================================
system_instruction = f"你是KBE冷气专家。语言：{lang}。简短回复。分析图片后必须加免责声明。预约：https://wa.me/6588972601"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 5. 聊天区
# ==========================================
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# ==========================================
# 6. 对话底栏 (上传 Icon + 输入框)
# ==========================================
st.markdown("---")
# 🎯 关键修改：在输入框正上方建立一列，专门放上传 Icon，右对齐贴近发送键
up_c1, up_c2 = st.columns([4, 1])
with up_c2:
    # 限制 50MB
    uploaded_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file and uploaded_file.size > 50 * 1024 * 1024:
        st.error("Max 50MB!")
        uploaded_file = None

if prompt := st.chat_input(hint):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant", avatar="❄️"):
        msg_ph = st.empty()
        content = [prompt]
        has_img = False
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            content.append(img)
            has_img = True
            st.session_state.messages.append({"role": "user", "content": "📸 [Photo Uploaded]"})

        response = st.session_state.chat_session.send_message(content)
        final_res = response.text + (disclaimer if has_img else "")
        msg_ph.markdown(final_res)
    
    st.session_state.messages.append({"role": "assistant", "content": final_res})

# 底部社交媒体
st.markdown(
    '<div style="text-align:center; font-size:12px; color:gray; margin-top:20px;">'
    '<a href="https://www.facebook.com/kbeaircon/">Facebook</a> | '
    '<a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | '
    '<a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | '
    '<a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">小红书</a>'
    '</div>', unsafe_allow_html=True
)

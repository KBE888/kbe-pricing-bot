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
    st.error("⚠️ 未找到 API Key！请检查 Secrets 配置。")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE AI 客服", page_icon="❄️", layout="centered")

# 极致优化 CSS
st.markdown(f"""
<style>
    .stFileUploader {{ padding-top: 0; }}
    div[data-testid="stHorizontalBlock"] {{ gap: 8px !important; }}
    .stChatInput {{ margin-top: -15px; }}
    .stButton>button {{ border-radius: 10px; height: 3em; }}
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
    title = "智能客服与报价助手"
    welcome = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断冷气故障。"
    hint = "描述问题或点击下方📷上传..."
    disclaimer = "\n\n> 💡 **温馨提示**：AI 图片分析结果仅供参考，实际请以师傅上门检查为准。"
    wa_n, call_n, web_n = "WhatsApp", "拨打中心", "官网"
else:
    title = "AI Service & Quote"
    welcome = "Hello! I am KBE expert. I can provide quotes or diagnose issues via photos."
    hint = "Describe issue or click 📷 below..."
    disclaimer = "\n\n> 💡 **Note**: AI diagnosis is for reference only. On-site inspection is recommended."
    wa_n, call_n, web_n = "WhatsApp", "Call Us", "Website"

st.markdown(f"<h3 style='color:{BRAND_COLOR};'>{title}</h3>", unsafe_allow_html=True)

# ==========================================
# 3. 三金刚按钮 (横向一排: Icon + 名字)
# ==========================================
b1, b2, b3 = st.columns(3)
b1.link_button(f"💬 {wa_n}", "https://wa.me/6588972601", use_container_width=True)
b2.link_button(f"📞 {call_n}", "tel:65067330", use_container_width=True)
b3.link_button(f"🌐 {web_n}", "https://www.kbe.com.sg/", use_container_width=True)

# ==========================================
# 4. 核心系统指令 (包含最新的检查费豁免政策)
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的冷气专家。语言：{lang}。
你的回复必须非常精简（2-3句）。

【核心政策 - 必须告知顾客】
1. 检查费：上门检查费为 $49。
2. 豁免政策：如果客户在检查后决定由我们进行维修，这 $49 的检查费将会被【豁免/抵扣】(Waive)。

【对话原则】
- 视觉诊断：分析图片给出可能的 1-2 个原因，并提醒客户上门检查。
- 报价：普通清洗 $49起，药水洗 $130起。先询问机型和台数再报总价。
- 引导预约：引导顾客点击 WhatsApp 链接 https://wa.me/6588972601。
"""

# ==========================================
# 5. 模型初始化
# ==========================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 6. 聊天记录显示
# ==========================================
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# ==========================================
# 7. 底部功能区 (上传 Icon + 输入框)
# ==========================================
st.markdown("---")
# 紧凑的上传区域
up_c1, up_c2 = st.columns([3, 1])
with up_c2:
    uploaded_file = st.file_uploader(
        "📷", 
        type=["jpg", "png", "jpeg"], 
        label_visibility="collapsed",
        help="Max 50MB"
    )
    if uploaded_file and uploaded_file.size > 50 * 1024 * 1024:
        st.error("Max 50MB!")
        uploaded_file = None

# 处理用户输入
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
            st.session_state.messages.append({"role": "user", "content": "📸 [用户发送了照片]"})

        try:
            response = st.session_state.chat_session.send_message(content)
            final_res = response.text + (disclaimer if has_img else "")
            msg_ph.markdown(final_res)
            st.session_state.messages.append({"role": "assistant", "content": final_res})
        except Exception as e:
            st.error(f"Error: {e}")

# 底部社交媒体链接
st.markdown(
    '<div style="text-align:center; font-size:12px; color:gray; margin-top:30px;">'
    '<a href="https://www.facebook.com/kbeaircon/">Facebook</a> | '
    '<a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | '
    '<a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | '
    '<a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">小红书</a>'
    '</div>', unsafe_allow_html=True
)

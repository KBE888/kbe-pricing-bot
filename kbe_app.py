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

# 极致优化 CSS
st.markdown(f"""
<style>
    /* 移除上传组件的多余边距 */
    .stFileUploader {{ padding-top: 0; }}
    /* 缩小按钮间距 */
    div[data-testid="stHorizontalBlock"] {{ gap: 5px !important; }}
    /* 调整聊天输入框与上方组件的距离 */
    .stChatInput {{ margin-top: -15px; }}
    /* 免责声明样式 */
    .disclaimer {{ font-size: 12px; color: #888; border-left: 2px solid {BRAND_COLOR}; padding-left: 10px; margin-top: 10px; }}
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
    welcome = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断故障。"
    hint = "描述问题..."
    disclaimer = "\n\n> 💡 **温馨提示**：AI 图片分析结果仅供参考，实际请以师傅上门检查为准。"
    wa_n, call_n, web_n = "WhatsApp", "拨打中心", "官网"
else:
    title = "AI Service & Quote"
    welcome = "Hello! I am KBE expert. I can provide quotes or diagnose issues via photos."
    hint = "Describe issue..."
    disclaimer = "\n\n> 💡 **Note**: AI diagnosis is for reference only. On-site inspection is recommended."
    wa_n, call_n, web_n = "WhatsApp", "Call Us", "Website"

st.markdown(f"<h3 style='color:{BRAND_COLOR};'>{title}</h3>", unsafe_allow_html=True)

# ==========================================
# 3. 三金刚按钮 (横向一排: Icon + 名字)
# ==========================================
# 使用 columns(3) 实现横向排布
b1, b2, b3 = st.columns(3)
b1.link_button(f"💬 {wa_n}", "https://wa.me/6588972601", use_container_width=True)
b2.link_button(f"📞 {call_n}", "tel:65067330", use_container_width=True)
b3.link_button(f"🌐 {web_n}", "https://www.kbe.com.sg/", use_container_width=True)

# ==========================================
# 4. 模型初始化
# ==========================================
system_instruction = f"你是KBE冷气专家。语言：{lang}。简短回复。分析图片后必须加免责声明。预约：https://wa.me/6588972601"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 5. 聊天记录显示
# ==========================================
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# ==========================================
# 6. 底部功能区 (输入框 + 紧贴下方的上传)
# ==========================================
st.markdown("---")

# 聊天输入框
prompt = st.chat_input(hint)

# 将上传按钮放在输入框下方，靠右对齐，模拟发送键旁边的位置
up_col1, up_col2 = st.columns([3, 1])
with up_col2:
    uploaded_file = st.file_uploader(
        "📷 (Max 50MB)", 
        type=["jpg", "png", "jpeg"], 
        label_visibility="collapsed"
    )

# 处理输入
if prompt or uploaded_file:
    # 简单的文件大小检查
    if uploaded_file and uploaded_file.size > 50 * 1024 * 1024:
        st.error("文件太大 (Max 50MB)！" if lang=="中文" else "File too large (Max 50MB)!")
    else:
        # 如果有输入，先添加到消息
        user_msg = prompt if prompt else "📸 [发送了一张照片]"
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"): st.write(user_msg)

        with st.chat_message("assistant", avatar="❄️"):
            msg_ph = st.empty()
            content = []
            if prompt: content.append(prompt)
            if uploaded_file:
                img = Image.open(uploaded_file)
                content.append(img)
            
            # 如果什么都没写也没发图（误触），不处理
            if content:
                response = st.session_state.chat_session.send_message(content)
                final_res = response.text + (disclaimer if uploaded_file else "")
                msg_ph.markdown(final_res)
                st.session_state.messages.append({"role": "assistant", "content": final_res})

# 底部社交媒体链接
st.markdown(
    '<div style="text-align:center; font-size:12px; color:gray; margin-top:30px;">'
    '<a href="https://www.facebook.com/kbeaircon/">Facebook</a> | '
    '<a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | '
    '<a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | '
    '<a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">小红书</a>'
    '</div>', unsafe_allow_html=True
)

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
# 1. 核心配置
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE ❄️ 智能客服", page_icon="❄️", layout="centered")

# ==========================================
# 2. 界面文本与语言处理
# ==========================================
top_col1, top_col2 = st.columns([1, 1])
with top_col1:
    st.image(LOGO_URL, width=150)
with top_col2:
    selected_lang = st.segmented_control(
        "Language / 语言", ["中文", "English"], 
        default=st.session_state.current_lang, key="lang_selector"
    )
    if selected_lang and selected_lang != st.session_state.current_lang:
        st.session_state.current_lang = selected_lang
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

lang = st.session_state.current_lang
if lang == "中文":
    title, subtitle = "智能客服与报价助手", "为您提供即时报价及专业的冷气疑难解答。"
    welcome_msg = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断故障。"
    chat_hint = "描述您的问题或上传照片..."
    upload_hint = "📸 点击上传照片"
    disclaimer = "\n\n> 💡 **温馨提示**：AI 图片分析结果仅供参考，实际情况可能因拍摄角度或光线有所差异。建议联系师傅上门以获取最精准的判断。"
else:
    title, subtitle = "AI Service & Quote", "Providing instant quotes and professional troubleshooting."
    welcome_msg = "Hello! I am KBE expert. I can provide quotes or diagnose issues via photos."
    chat_hint = "Describe your issue or upload photo..."
    upload_hint = "📸 Click to upload photo"
    disclaimer = "\n\n> 💡 **Friendly Note**: AI image analysis is for reference only. Actual issues may vary due to photo quality. We recommend a technician's on-site inspection for accurate diagnosis."

st.markdown(f"<h2 style='color:{BRAND_COLOR}; margin-top:-10px;'>{title}</h2>", unsafe_allow_html=True)
st.caption(subtitle)

# 快速联系按钮
st.markdown("---")
b1, b2, b3 = st.columns(3)
b1.markdown("[![WA](https://img.shields.io/badge/WhatsApp-25D366?style=flat&logo=whatsapp&logoColor=white)](https://wa.me/6588972601)")
b2.markdown("[![Call](https://img.shields.io/badge/Call-0078D4?style=flat&logo=phone&logoColor=white)](tel:65067330)")
b3.markdown("[![Web](https://img.shields.io/badge/Website-gray?style=flat)](https://www.kbe.com.sg/)")

# ==========================================
# 3. AI 模型设置
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的专家。语言：{lang}。
1. 视觉诊断：分析图片原因，回复精简（2-3句）。
2. 重要：在分析完图片后，必须提醒客户 AI 诊断仅供参考。
3. 预约：引导点击 WhatsApp https://wa.me/6588972601。
"""
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 聊天界面与“对话框内”上传
# ==========================================
# 显示历史消息
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome_msg)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# --- 模拟对话框内的上传按钮 ---
# 在输入框上方放置一个小的上传组件，模拟在对话框内部的操作
with st.container():
    uploaded_file = st.file_uploader(upload_hint, type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if prompt := st.chat_input(chat_hint):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant", avatar="❄️"):
        msg_ph = st.empty()
        content = [prompt]
        is_image = False
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            content.append(img)
            is_image = True
            st.session_state.messages.append({"role": "user", "content": "📸 [Photo Uploaded]"})

        response = st.session_state.chat_session.send_message(content)
        final_text = response.text
        
        # 如果有图片，追加免责声明
        if is_image:
            final_text += disclaimer
            
        msg_ph.markdown(final_text)
    
    st.session_state.messages.append({"role": "assistant", "content": final_text})

# 底部链接
st.markdown("---")
st.markdown('<div style="text-align: center; font-size: 12px; color: gray;">'
            '<a href="https://www.facebook.com/kbeaircon/">Facebook</a> | '
            '<a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | '
            '<a href="https://www.tiktok.com/@kbe_aircon">TikTok</a></div>', unsafe_allow_html=True)

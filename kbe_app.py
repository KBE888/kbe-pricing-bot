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

# 极致优化 CSS，缩小间距，美化按钮
st.markdown(f"""
<style>
    div[data-testid="stHorizontalBlock"] {{ gap: 5px !important; }}
    .stButton>button {{ border-radius: 8px; height: 2.5em; font-size: 14px; }}
    .stChatInput {{ margin-top: -20px; }}
    /* 隐藏上传组件的多余文字，只留图标 */
    .stFileUploader section {{ padding: 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏：找回消失的公司信息
# ==========================================
with st.sidebar:
    st.image(LOGO_URL, width=200)
    st.markdown("---")
    if st.session_state.current_lang == "中文":
        st.header("🏢 公司资讯")
        st.markdown("""
        **🕒 办公时间:**
        - 周一至五: 8:30 AM - 5:30 PM
        - 周六: 8:30 AM - 12:30 PM
        - 周日及公假: 休息
        
        **📍 总部地址:**
        - Blk 1014 Geylang East Ave 3 
        - #02-236, Singapore 389729
        
        **☎️ 联络电话:**
        - 办公室: 6506 7330
        - 24小时热线: 8897 2601
        """)
    else:
        st.header("🏢 Company Info")
        st.markdown("""
        **🕒 Office Hours:**
        - Mon-Fri: 8:30 AM - 5:30 PM
        - Sat: 8:30 AM - 12:30 PM
        - Sun & PH: Closed
        
        **📍 Address:**
        - Blk 1014 Geylang East Ave 3 
        - #02-236, Singapore 389729
        
        **☎️ Contact:**
        - Office: 6506 7330
        - 24h Hotline: 8897 2601
        """)
    st.markdown("---")
    if st.button("🗑️ 清空对话 / Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# ==========================================
# 3. 首页顶部 (Logo & 语言切换)
# ==========================================
t_col1, t_col2 = st.columns([1, 1])
with t_col1:
    st.image(LOGO_URL, width=120)
with t_col2:
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
title = "智能客服与报价助手" if lang=="中文" else "AI Quote Assistant"
st.markdown(f"<h3 style='color:{BRAND_COLOR}; margin-top:-10px;'>{title}</h3>", unsafe_allow_html=True)

# ==========================================
# 4. 横向导航按钮 (并排显示)
# ==========================================
b1, b2, b3 = st.columns(3)
b1.link_button("💬 WhatsApp", "https://wa.me/6588972601", use_container_width=True)
b2.link_button("📞 拨打电话", "tel:65067330", use_container_width=True)
b3.link_button("🌐 官方网站", "https://www.kbe.com.sg/", use_container_width=True)

# ==========================================
# 5. 模型初始化
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的冷气专家。语言：{lang}。回复简短（2句）。
【重要政策】上门检查费 $49，如果后期由我们维修，这 $49 会被 Waive (豁免/抵扣)。
【报价】普通洗 $49起，药水洗 $130起。
【视觉诊断】分析图片原因，必加免责声明：AI 诊断仅供参考，实际以师傅上门为准。
"""
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 6. 聊天记录显示
# ==========================================
st.markdown("---")
if not st.session_state.messages:
    welcome = "您好！请问今天有什么可以帮您？您可以直接拍照发给我诊断故障。" if lang=="中文" else "Hello! How can I help you today? You can send a photo for diagnosis."
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# ==========================================
# 7. 对话底栏 (相机 Icon + 输入框)
# ==========================================
# 我们在输入框正上方创造一个非常紧凑的上传区
up_col1, up_col2 = st.columns([4, 1])
with up_col2:
    # 限制 50MB，相机图标
    uploaded_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file and uploaded_file.size > 50 * 1024 * 1024:
        st.error("Max 50MB!")
        uploaded_file = None

prompt = st.chat_input("描述问题..." if lang=="中文" else "Describe issue...")

if prompt or uploaded_file:
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
            
        try:
            response = st.session_state.chat_session.send_message(content)
            final_res = response.text
            # 自动加免责声明
            if uploaded_file:
                final_res += ("\n\n> 💡 提示：AI 图片分析仅供参考，实际请以师傅检查为准。" if lang=="中文" else "\n\n> 💡 Note: AI analysis is for reference only.")
            msg_ph.markdown(final_res)
            st.session_state.messages.append({"role": "assistant", "content": final_res})
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 8. 底部社交媒体
# ==========================================
st.markdown(
    '<div style="text-align:center; font-size:12px; color:gray; margin-top:30px;">'
    '<a href="https://www.facebook.com/kbeaircon/">Facebook</a> | '
    '<a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | '
    '<a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | '
    '<a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">小红书</a>'
    '</div>', unsafe_allow_html=True
)

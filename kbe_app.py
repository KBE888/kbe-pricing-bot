import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# ==========================================
# 0. 核心状态初始化
# ==========================================
st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_lang", "中文")
st.session_state.setdefault("chat_session", None)

# ==========================================
# 1. 配置与视觉样式
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！请在 Streamlit Cloud Secrets 中配置。")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE AI 客服", page_icon="❄️", layout="centered")

# 极致优化移动端布局
st.markdown(f"""
<style>
    div[data-testid="stHorizontalBlock"] {{ gap: 5px !important; }}
    .stButton>button {{ border-radius: 8px; height: 2.8em; font-size: 14px; border: 1px solid #eee; }}
    .stChatInput {{ margin-top: -20px; }}
    .stFileUploader section {{ padding: 0 !important; }}
    /* 侧边栏样式优化 */
    [data-testid="stSidebar"] {{ background-color: #f8f9fa; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏：公司核心资讯 (更新了新地址)
# ==========================================
with st.sidebar:
    st.image(LOGO_URL, width=180)
    st.markdown("---")
    if st.session_state.current_lang == "中文":
        st.header("🏢 公司信息")
        st.markdown(f"""
        **📍 办公地址:**
        53 Ubi Ave 1, #03-47
        Paya Ubi Industrial Park,
        Singapore 408934
        
        **🕒 营业时间:**
        - 周一至五: 8:30 AM - 5:30 PM
        - 周六: 8:30 AM - 12:30 PM
        
        **☎️ 联络方式:**
        - 办公室: `65067330`
        - 24h热线: `88972601`
        """)
    else:
        st.header("🏢 Company Info")
        st.markdown(f"""
        **📍 Address:**
        53 Ubi Ave 1, #03-47
        Paya Ubi Industrial Park,
        Singapore 408934
        
        **🕒 Operating Hours:**
        - Mon-Fri: 8:30 AM - 5:30 PM
        - Sat: 8:30 AM - 12:30 PM
        
        **☎️ Contact:**
        - Office: `65067330`
        - 24h Hotline: `88972601`
        """)
    st.markdown("---")
    if st.button("🗑️ 清空对话 / Clear"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# ==========================================
# 3. 首页顶部 (Logo 与 语言切换)
# ==========================================
t_col1, t_col2 = st.columns([1, 1])
with t_col1:
    st.image(LOGO_URL, width=110)
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
# 4. 横向快捷导航 (三金刚按钮)
# ==========================================
b1, b2, b3 = st.columns(3)
b1.link_button("💬 WhatsApp", "https://wa.me/6588972601", use_container_width=True)
b2.link_button("📞 拨打电话", "tel:65067330", use_container_width=True)
b3.link_button("🌐 官方网站", "https://www.kbe.com.sg/", use_container_width=True)

# ==========================================
# 5. 模型初始化与商业逻辑
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的冷气专家。语言：{lang}。
【重要商业政策】
1. 检查费：上门检查收 $49。
2. 豁免政策：如果检查后客户同意由我们维修，这 $49 检查费将直接豁免/抵扣 (Waive)。
3. 报价基础：普通清洗 $49起，药水洗 $130起。
4. 视觉诊断：分析照片原因，回复须精简（2句内）。
5. 免责声明：图片分析后必须说明“AI诊断仅供参考，以师傅现场检查为准”。
"""
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 6. 聊天历史显示
# ==========================================
st.markdown("---")
if not st.session_state.messages:
    welcome = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断冷气故障。" if lang=="中文" else "Hello! I'm KBE expert. I can provide quotes or diagnose issues via photos."
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# ==========================================
# 7. 对话底栏 (相机图标 + 输入框)
# ==========================================
# 紧凑的上传列布局
up_c1, up_c2 = st.columns([4, 1])
with up_c2:
    # 限制 50MB，相机图标
    uploaded_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file and uploaded_file.size > 50 * 1024 * 1024:
        st.error("Max 50MB!")
        uploaded_file = None

prompt = st.chat_input("描述问题或上传照片..." if lang=="中文" else "Describe issue or upload photo...")

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
            if uploaded_file:
                final_res += ("\n\n> 💡 提示：AI 图片分析仅供参考，实际以师傅检查为准。" if lang=="中文" else "\n\n> 💡 Note: AI analysis is for reference only.")
            msg_ph.markdown(final_res)
            st.session_state.messages.append({"role": "assistant", "content": final_res})
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# 8. 底部社交媒体链接
# ==========================================
st.markdown(
    '<div style="text-align:center; font-size:12px; color:gray; margin-top:30px;">'
    '<a href="https://www.facebook.com/kbeaircon/">Facebook</a> | '
    '<a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | '
    '<a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | '
    '<a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">小红书</a>'
    '</div>', unsafe_allow_html=True
)

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
    st.error("⚠️ 未找到 API Key！请在 Secrets 中配置。")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE 智能客服", page_icon="❄️", layout="centered")

# 极致优化移动端 UI
st.markdown(f"""
<style>
    div[data-testid="stHorizontalBlock"] {{ gap: 5px !important; }}
    .stButton>button {{ border-radius: 8px; height: 2.8em; font-size: 13px; border: 1px solid #eee; }}
    .stChatInput {{ margin-top: -20px; }}
    .stFileUploader section {{ padding: 0 !important; }}
    .social-links {{ text-align: center; font-size: 12px; margin: 10px 0; }}
    .social-links a {{ text-decoration: none; color: {BRAND_COLOR}; margin: 0 8px; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏：公司核心资讯 (地址/时间/价格说明)
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
        
        **💰 费用说明:**
        - 单独检查费: $49
        - **优惠**: 若进行维修/清洗，检查费全额免除 (Waive)。
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
        
        **💰 Fee Policy:**
        - Transport/Inspection: $49
        - **Offer**: Waived if you proceed with service/repair.
        """)
    st.markdown("---")
    if st.button("🗑️ 清空对话 / Clear Chat"):
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
st.markdown(f"<h3 style='color:{BRAND_COLOR}; margin-top:-10px;'>{'KBE 智能客服' if lang=='中文' else 'KBE AI Service'}</h3>", unsafe_allow_html=True)

# ==========================================
# 4. 横向快捷导航 (WhatsApp/Call/Web) & 社交媒体
# ==========================================
b1, b2, b3 = st.columns(3)
b1.link_button("💬 WhatsApp", "https://wa.me/6588972601", use_container_width=True)
b2.link_button("📞 拨打电话" if lang=="中文" else "📞 Call Us", "tel:65067330", use_container_width=True)
b3.link_button("🌐 官方网站" if lang=="中文" else "🌐 Website", "https://www.kbe.com.sg/", use_container_width=True)

st.markdown(f"""
<div class="social-links">
    <a href="https://www.facebook.com/kbeaircon/">Facebook</a> | 
    <a href="https://www.instagram.com/kbe_aircon/">Instagram</a> | 
    <a href="https://www.tiktok.com/@kbe_aircon">TikTok</a> | 
    <a href="https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4">{'小红书' if lang=='中文' else 'Xiaohongshu'}</a>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. 核心 AI 逻辑 (强化检查费逻辑)
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的冷气专家。语言：{lang}。回复非常精简（2句内）。

【关于检查费的解释逻辑（重中之重）】
1. 如果顾客问“价格包含检查费吗”或类似问题：
   - 明确告知：我们的服务报价（如$49清洗费）已经包含了上门检查的费用。
   - 只有在“仅检查、不进行任何维修或清洗”的情况下，才单独收取 $49 检查费。
   - 总结一句话：只要您修/洗冷气，检查费就是免费的。

【详细价格表】
1. 普通清洗 (Normal Wash) - 壁挂式: 
   - 1台: $49 | 2台: $64 | 3台: $96 | 4台: $116 | 5台: $140
   - (天花板机/风管机：每台加收 $5)
2. 药水清洁 (Chemical Wash) - 壁挂式: 
   - 9-12k BTU: $130/台 | 18k BTU: $200/台 | 24k BTU: $230/台
3. 补充冷媒: R410a: $110起 | R32: $145起。

【对话原则】
- 视觉诊断：分析图片给原因。
- 引导预约：https://wa.me/6588972601
"""

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
if st.session_state.chat_session is None:
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 6. 聊天区域
# ==========================================
st.markdown("---")
if not st.session_state.messages:
    welcome = "您好！我是 KBE 专家。我可以为您报价，或通过照片诊断冷气故障。" if lang=="中文" else "Hello! I'm KBE expert. I can provide quotes or diagnose issues via photos."
    with st.chat_message("assistant", avatar="❄️"): st.write(welcome)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

# ==========================================
# 7. 对话底栏 (相机上传 + 输入框)
# ==========================================
up_c1, up_c2 = st.columns([4, 1])
with up_c2:
    uploaded_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], label_visibility="collapsed", help="Max 50MB")
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
                final_res += ("\n\n> 💡 提示：AI 图片分析仅供参考，实际以师傅现场检查为准。" if lang=="中文" else "\n\n> 💡 Note: AI analysis is for reference only.")
            msg_ph.markdown(final_res)
            st.session_state.messages.append({"role": "assistant", "content": final_res})
        except Exception as e:
            st.error(f"Error: {e}")

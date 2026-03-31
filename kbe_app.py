import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 0. 核心初始化 (确保无报错运行)
# ==========================================
st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_lang", "中文")
st.session_state.setdefault("chat_session", None)

# ==========================================
# 1. 核心配置与品牌信息
# ==========================================
try:
    # 确保你已在 Streamlit Cloud 的 Secrets 中设置了 GEMINI_API_KEY
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！请在 Streamlit Cloud Secrets 中配置。")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE ❄️ 智能客服", page_icon="❄️", layout="centered")

# 自定义 CSS 样式
st.markdown(f"""
<style>
    [data-testid="stSidebarNav"] {{ border-right: 1px solid #f0f2f6; }}
    div[data-testid="stChatInput"] input:focus {{ border-color: {BRAND_COLOR}; }}
    .stButton>button {{ background-color: {BRAND_COLOR}; color: white; border-radius: 20px; border: none; padding: 5px 15px; }}
    .stButton>button:hover {{ background-color: {BRAND_COLOR}aa; color: white; }}
    [data-testid="stChatMessageAssistant"] .stChatMessageContent div.stMarkdown {{ border-left: 3px solid {BRAND_COLOR}; padding-left: 10px; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏：语言切换、公司信息与社交媒体 (含 WhatsApp)
# ==========================================
with st.sidebar:
    st.image(LOGO_URL, width=220)
    st.markdown("---")
    
    st.header("🌐 Language / 语言")
    default_index = 0 if st.session_state.current_lang == "中文" else 1
    selected_lang = st.radio("选择语言:", ["中文", "English"], index=default_index, label_visibility="collapsed")
    
    # 侦测语言切换
    if selected_lang != st.session_state.current_lang:
        st.session_state.current_lang = selected_lang
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

    st.markdown("---")
    
    # 根据语言显示联系信息与社交媒体链接
    if st.session_state.current_lang == "中文":
        st.header("📞 联系我们")
        st.markdown(f"""
        **🕒 营业时间:**
        - 周一至五: 8:30 AM - 5:30 PM
        - 周六: 8:30 AM - 12:30 PM
        
        **📱 快速联系:**
        - 📞 电话: [65067330](tel:65067330)
        - 💬 WhatsApp: [88972601](https://wa.me/6588972601)
        
        **🌐 关注我们:**
        - 🏠 [官方网站](https://www.kbe.com.sg/)
        - 🔵 [Facebook](https://www.facebook.com/kbeaircon/)
        - 📸 [Instagram](https://www.instagram.com/kbe_aircon/)
        - 📺 [YouTube](https://www.youtube.com/@kbeairconditioningengineer4458)
        - 📕 [小红书](https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4)
        - 🎵 [TikTok](https://www.tiktok.com/@kbe_aircon)
        """)
    else:
        st.header("📞 Contact Us")
        st.markdown(f"""
        **🕒 Operating Hours:**
        - Mon-Fri: 8:30 AM - 5:30 PM
        - Sat: 8:30 AM - 12:30 PM
        
        **📱 Quick Contact:**
        - 📞 Tel: [65067330](tel:65067330)
        - 💬 WhatsApp: [88972601](https://wa.me/6588972601)
        
        **🌐 Follow Us:**
        - 🏠 [Official Website](https://www.kbe.com.sg/)
        - 🔵 [Facebook](https://www.facebook.com/kbeaircon/)
        - 📸 [Instagram](https://www.instagram.com/kbe_aircon/)
        - 📺 [YouTube](https://www.youtube.com/@kbeairconditioningengineer4458)
        - 📕 [Xiaohongshu](https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4)
        - 🎵 [TikTok](https://www.tiktok.com/@kbe_aircon)
        """)

    st.markdown("---")
    st.header("⚙️ 对话控制")
    if st.button("🗑️ 清空对话 / Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# ==========================================
# 3. 界面文本设置
# ==========================================
if st.session_state.current_lang == "中文":
    title_text = "智能客服与报价助手"
    subtitle_text = "为您提供即时报价及专业的冷气疑难解答。"
    welcome_msg = "您好！我是 KBE 智能客服及冷气专家。请问今天需要询价，还是有冷气方面的问题需要解答？"
    chat_placeholder = "例如：洗两台冷气大概多少钱？"
    calc_msg = "KBE 客服正在思考中..."
    error_msg = "⚠️ 抱歉，遇到错误："
else:
    title_text = "AI Customer Service"
    subtitle_text = "Providing instant quotes and professional aircon troubleshooting."
    welcome_msg = "Hello! I am the KBE AI Customer Service. Do you need a quote today, or have any questions about your aircon?"
    chat_placeholder = "e.g., How much to wash 2 aircons?"
    calc_msg = "KBE AI is thinking..."
    error_msg = "⚠️ Sorry, an error occurred:"

# 界面头部渲染
col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.markdown(f"<h1 style='color:{BRAND_COLOR}; padding-top:10px;'>{title_text}</h1>", unsafe_allow_html=True)
st.caption(subtitle_text)

# ==========================================
# 4. AI 核心指令 (含 WhatsApp 引导)
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的专属在线客服。语言：{st.session_state.current_lang}。

【对话原则】
1. 极度简短：回复控制在2-3句。
2. 循序渐进反问：先问机型（壁挂/天花板）、数量、清洗类型（普通/药水），再给总价。
3. 引导预约：报价后，引导顾客点击侧边栏的 WhatsApp 链接或直接点击：https://wa.me/6588972601 预约。

【KBE 官方信息】
- 营业时间：Mon-Fri 8:30am-5:30pm, Sat 8:30am-12:30pm。
- 联系电话：65067330 | 手机/WhatsApp：88972601。

【KBE 价目表】(内部计算用)
1. 普通清洗 - 壁挂式: 1台:$49 | 2台:$64 | 3台:$96 | 4台:$116 | 5台:$140 (Ceiling 机每台加 $5)
2. 药水清洁 - 壁挂式: 9-12k BTU:$130 | 18k BTU:$200 | 24k BTU:$230
3. 补充冷媒: R410a: 0-100PSI:$110 | 101-130PSI:$165 | 131-160PSI:$200。R32: 0-100PSI:$145 | 101-130PSI:$200 | 131-160PSI:$220。
"""

# ==========================================
# 5. 模型初始化与逻辑
# ==========================================
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
    if st.session_state.chat_session is None:
        st.session_state.chat_session = model.start_chat(history=[])
except Exception as e:
    st.error(f"API 初始化失败: {e}")
    st.stop()

if len(st.session_state.messages) == 0:
    with st.chat_message("assistant", avatar="❄️"):
        st.markdown(f"<div style='color:{BRAND_COLOR};'>{welcome_msg}</div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="❄️" if msg["role"]=="assistant" else None):
        st.markdown(msg["content"])

if prompt := st.chat_input(chat_placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="❄️"):
        status_ph = st.empty()
        status_ph.write(calc_msg)
        try:
            response = st.session_state.chat_session.send_message(prompt, stream=True)
            full_res = ""
            msg_ph = st.empty()
            for chunk in response:
                if chunk.text:
                    status_ph.empty()
                    full_res += chunk.text
                    msg_ph.markdown(full_res + " ▌")
                    time.sleep(0.01)
            msg_ph.markdown(full_res)
        except Exception as e:
            status_ph.empty()
            full_res = f"{error_msg}\n\n`{str(e)}`"
            st.markdown(full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})

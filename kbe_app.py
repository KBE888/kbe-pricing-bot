import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 0. 暴力初始化 (绝对不可能再报错)
# ==========================================
st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_lang", "中文")
st.session_state.setdefault("chat_session", None)

# ==========================================
# 1. 核心配置与品牌信息
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

st.set_page_config(page_title="KBE ❄️ 智能客服", page_icon="❄️", layout="centered")
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
# 公司信息展示 (带图标和链接版)
    if st.session_state.current_lang == "中文":
        st.header("📞 联系我们")
        st.markdown(f"""
        **🕒 营业时间:**
        - 周一至五: 8:30AM - 5:30PM
        - 周六: 8:30AM - 12:30PM
        
        **📱 联系方式:**
        - 📞 电话: [65067330](tel:65067330)
        - 💬 手机: [88972601](https://wa.me/6588972601)
        
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
        - Mon-Fri: 8:30AM - 5:30PM
        - Sat: 8:30AM - 12:30PM
        
        **📱 Contact Info:**
        - 📞 Tel: [65067330](tel:65067330)
        - 💬 Mobile: [88972601](https://wa.me/6588972601)
        
        **🌐 Follow Us:**
        - 🏠 [Website](https://www.kbe.com.sg/)
        - 🔵 [Facebook](https://www.facebook.com/kbeaircon/)
        - 📸 [Instagram](https://www.instagram.com/kbe_aircon/)
        - 📺 [YouTube](https://www.youtube.com/@kbeairconditioningengineer4458)
        - 📕 [Xiaohongshu](https://www.xiaohongshu.com/user/profile/618a1a3a00000000010257e4)
        - 🎵 [TikTok](https://www.tiktok.com/@kbe_aircon)
        """)
    
    st.header("🌐 Language / 语言")
    default_index = 0 if st.session_state.current_lang == "中文" else 1
    selected_lang = st.radio("Choose:", ["中文", "English"], index=default_index, label_visibility="collapsed")
    
    if selected_lang != st.session_state.current_lang:
        st.session_state.current_lang = selected_lang
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

    st.markdown("---")
    if st.session_state.current_lang == "中文":
        st.header("📞 联系我们")
        st.markdown("**🕒 营业时间:**\n- 周一至五: 8:30AM-5:30PM\n- 周六: 8:30AM-12:30PM\n\n**📱 联系方式:**\n- 电话: 65067330\n- 手机: 88972601\n\n**🌐 了解更多:**\n- 网站: www.kbe.com.sg\n- 社交: Facebook, Instagram, 小红书, TikTok")
    else:
        st.header("📞 Contact Us")
        st.markdown("**🕒 Operating Hours:**\n- Mon-Fri: 8:30AM-5:30PM\n- Sat: 8:30AM-12:30PM\n\n**📱 Contact Info:**\n- Tel: 65067330\n- Mobile: 88972601\n\n**🌐 Find Out More:**\n- Website: www.kbe.com.sg\n- Social: Facebook, Instagram, Xiaohongshu, TikTok")

    st.markdown("---")
    st.header("⚙️ 对话控制")
    if st.button("🗑️ 清空对话 / Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# ==========================================
# 3. 界面文本与头部
# ==========================================
if st.session_state.current_lang == "中文":
    title_text = "智能客服与报价助手"
    subtitle_text = "为您提供即时报价及专业的冷气疑难解答。"
    welcome_msg = "您好！我是 KBE 智能客服及冷气专家。请问今天需要询价，还是有冷气方面的问题需要解答？"
    chat_placeholder = "例如：洗两台冷气大概多少钱？ / 冷气漏水怎么办？"
    calc_msg = "KBE 客服正在思考中..."
    error_msg = "⚠️ 抱歉，遇到错误："
else:
    title_text = "AI Customer Service"
    subtitle_text = "Providing instant quotes and professional aircon troubleshooting."
    welcome_msg = "Hello! I am the KBE AI Customer Service. Do you need a quote today, or have any questions about your aircon?"
    chat_placeholder = "e.g., How much to wash 2 aircons?"
    calc_msg = "KBE AI is thinking..."
    error_msg = "⚠️ Sorry, an error occurred:"

col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.markdown(f"<h1 style='color:{BRAND_COLOR}; padding-top:10px;'>{title_text}</h1>", unsafe_allow_html=True)
st.caption(subtitle_text)

# ==========================================
# 4. AI 指令 (拒绝发长表，强制反问)
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的专属在线客服。语言：{st.session_state.current_lang}。

【核心原则】
1. 极度简短：每次回复2-3句话。绝对不要一次性发整个价目表！
2. 循序渐进反问：当顾客问价格时，先反问获取细节（如：几台？普通还是药水？壁挂还是天花板机？）。
3. 引导预约：电话 65067330 或手机 88972601。

【KBE 价目表】(仅供内部计算，禁止直接发给顾客)
1. 普通清洗 - 壁挂式: 1台:$49 | 2台:$64 | 3台:$96 | 4台:$116 | 5台:$140 (Ceiling/Ducted 每台加 $5)
2. 药水清洁 - 壁挂式: 9-12k BTU:$130 | 18k BTU:$200 | 24k BTU:$230 (Ceiling药水洗需人工报价)
3. 补充氟利昂: R410a: 0-100PSI:$110 | 101-130PSI:$165 | 131-160PSI:$200 | 满筒:$320。R32: 0-100PSI:$145 | 101-130PSI:$200 | 131-160PSI:$220。
"""

# ==========================================
# 5. 模型初始化与渲染
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
                    time.sleep(0.02)
            msg_ph.markdown(full_res)
        except Exception as e:
            status_ph.empty()
            full_res = f"{error_msg}\n\n`{str(e)}`"
            st.markdown(full_res)
    st.session_state.messages.append({"role": "assistant", "content": full_res})

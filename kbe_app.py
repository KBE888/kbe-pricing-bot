import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 0. 核心配置与品牌信息
# ==========================================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！请确保 `.streamlit/secrets.toml` 文件已正确配置。")
    st.stop()

BRAND_COLOR = "#199ad6"
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

# ==========================================
# 1. 页面基本设置与界面美化
# ==========================================
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
# 2. 侧边栏：语言选择与控制
# ==========================================
with st.sidebar:
    st.image(LOGO_URL, width=220)
    st.markdown("---")
    
    st.header("🌐 Language / 语言")
    # 语言选择器
    selected_lang = st.radio("Choose your preferred language:", ["中文", "English"], label_visibility="collapsed")
    
    st.markdown("---")
    st.header("⚙️ 对话控制 / Controls")
    if st.button("🗑️ 清空对话 / Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()
    st.markdown(f'<div style="text-align:center; color:#777; font-size:12px; margin-top:20px;">KBE All rights reserved.</div>', unsafe_allow_html=True)

# 侦测语言是否发生切换，如果切换了，清空历史记录并重置模型
if "current_lang" not in st.session_state:
    st.session_state.current_lang = selected_lang

if st.session_state.current_lang != selected_lang:
    st.session_state.current_lang = selected_lang
    st.session_state.messages = []
    st.session_state.chat_session = None
    st.rerun()

# 根据选择的语言设置界面文本
if selected_lang == "中文":
    title_text = "智能客服与报价助手"
    subtitle_text = "为您提供即时报价及专业的冷气疑难解答。"
    welcome_msg = "您好！我是 KBE 智能客服及冷气专家。请问今天需要询价，还是有冷气方面的问题需要解答？"
    chat_placeholder = "例如：洗两台冷气多少钱？ / 冷气漏水怎么办？"
    calc_msg = "KBE 客服正在思考中..."
    error_msg = "⚠️ 开发者调试信息 - 抱歉，程序遇到了错误："
else:
    title_text = "AI Customer Service"
    subtitle_text = "Providing instant quotes and professional aircon troubleshooting."
    welcome_msg = "Hello! I am the KBE AI Customer Service and Aircon Expert. Do you need a quote today, or do you have any questions about your aircon?"
    chat_placeholder = "e.g., How much to wash 2 aircons? / Why is my aircon leaking?"
    calc_msg = "KBE AI is thinking..."
    error_msg = "⚠️ Developer Debug - Sorry, an error occurred:"

# ==========================================
# 3. 界面头部
# ==========================================
col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.markdown(f"<h1 style='color:{BRAND_COLOR}; padding-top:10px;'>{title_text}</h1>", unsafe_allow_html=True)
st.caption(subtitle_text)

# ==========================================
# 4. 核心系统指令 (升级为冷气专家)
# ==========================================
system_instruction = f"""
你现在是 KBE 公司的专属在线客服，同时也是一名拥有多年经验的【专业冷气维修专家】。
当前顾客选择的语言是：{selected_lang}。你必须**严格且完全地使用 {selected_lang}** 进行回复！

你的核心任务是：
1. 根据 KBE 价目表提供准确报价。
2. 运用专业知识，耐心解答顾客关于冷气机的一般性故障问题（如漏水、不冷、异响、结冰等）以及日常保养建议。
3. 态度专业、热情，并在解答故障时，自然地引导顾客预约 KBE 的上门检查或清洗服务。

【KBE 官方服务价目表】
1. 普通清洗 (Normal Wash) - 壁挂式空调 (Wall-mounted)
- 1 台：$49
- 2 台：$64
- 3 台：$96
- 4 台：$116
- 5 台：$140
*附加费：如果是 Ceiling cassette 或 Ducted unit，每台需要在上述基础价格上额外加收 $5。

2. 药水清洁 (Chemical Wash) - 壁挂式空调 (Wall-mounted)
- 9,000 ~ 12,000 BTU：$130 / 台
- 18,000 BTU：$200 / 台
- 24,000 BTU：$230 / 台
*注意：如果是 Ceiling cassette 或 Ducted unit 的药水清洁，必须告知顾客需要联系人工客服获取准确报价。

3. 补充氟利昂/冷媒 (Top up Gas) 价格
R410a: 0~100 PSI: $110 | 101~130 PSI: $165 | 131~160 PSI: $200 | 满筒(VRV): $320
R32: 0~100 PSI: $145 | 101~130 PSI: $200 | 131~160 PSI: $220

4. 杂项附加费
- 高空作业或需要高楼梯作业：需另外收费 $20 ~ $50（具体需现场评估）。

【KBE 标准清洗服务准则 (13项)】
如果顾客询问清洗包含什么，请向他们列出：检查气体压力、清洁蒸发器盘管、清洁过滤网、清洁排水盘、清理排水管、检查电子元件、检查冷气设置、检查泄漏、测试排水流量、润滑部件、检查冷却气压、检查温度、检查气流量。

【客服绝对红线与行为规则】
1. 报价底线：针对价目表上有的服务，直接计算总价。对于【价目表上没有的任何维修项目或特殊机型清洗】，**绝对不要自行捏造价格**，必须礼貌告知：“这种情况需要专业师傅现场评估”，并提供联系方式。
2. 专家解答：如果顾客描述冷气故障（例如漏水），你应该先给出专业的分析（例如：通常是因为排水管堵塞、过滤网太脏或冷媒不足），然后建议他们进行清洗或检查。
3. 拒绝讲价：统一定价，委婉拒绝折扣要求。
4. 引导预约：在对话中合适的时候，告诉顾客：“如需预约服务或进一步咨询，请在常规工作时间联系 88972601。”
"""

# ==========================================
# 5. 初始化模型与对话
# ==========================================
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )
    if "chat_session" not in st.session_state or st.session_state.chat_session is None:
        st.session_state.chat_session = model.start_chat(history=[])
except Exception as e:
    st.error(f"API Initialization failed: {e}")
    st.stop()

# ==========================================
# 6. 渲染聊天界面
# ==========================================
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"):
        st.markdown(f"<div style='color:{BRAND_COLOR};'>{welcome_msg}</div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    avatar = "❄️" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input(chat_placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="❄️"):
        status_placeholder = st.empty()
        status_placeholder.write(calc_msg)
        
        try:
            response = st.session_state.chat_session.send_message(prompt, stream=True)
            full_response = ""
            
            # ✅ 打字机修复：在循环外部创建一个固定的文字框
            message_placeholder = st.empty()
            
            for chunk in response:
                if chunk.text:
                    status_placeholder.empty()
                    full_response += chunk.text
                    # ✅ 让新字不断刷新在这个固定的框里，加上打字光标 ▌
                    message_placeholder.markdown(full_response + " ▌")
                    time.sleep(0.02) 
            
            # ✅ 循环结束后，去掉光标，打印最终完整的话
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            status_placeholder.empty()
            full_response = f"{error_msg}\n\n`{str(e)}`"
            st.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})

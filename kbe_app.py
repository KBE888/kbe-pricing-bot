import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 0. 核心配置与品牌信息 (安全读取版)
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
st.set_page_config(page_title="KBE ❄️ 智能报价客服", page_icon="❄️", layout="centered")

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
# 2. 界面头部
# ==========================================
st.sidebar.image(LOGO_URL, width=220)
st.sidebar.title("❄️ KBE 客服系统")
st.sidebar.caption(f"powered by Gemini 1.5 Flash")

col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.markdown(f"<h1 style='color:{BRAND_COLOR}; padding-top:10px;'>智能报价助手</h1>", unsafe_allow_html=True)
st.caption("基于 KBE 标准服务价目表为您提供即时报价。")

# ==========================================
# 3. 系统指令 (System Instructions)
# ==========================================
system_instruction = """
你现在是 KBE 公司的专属在线客服。你的态度必须专业、热情、且回答要简明扼要，绝对不要废话。请根据顾客使用的语言（中文或英文）进行回复。

你的核心任务是：根据以下唯一的价目表为顾客提供准确的报价，并引导他们预约。

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
R410a:
- 0 ~ 100 PSI：$110
- 101 ~ 130 PSI：$165
- 131 ~ 160 PSI：$200
- 满筒 (Per cylinder for VRV)：$320
R32:
- 0 ~ 100 PSI：$145
- 101 ~ 130 PSI：$200
- 131 ~ 160 PSI：$220

4. 杂项附加费
- 高空作业或需要高楼梯作业：需另外收费 $20 ~ $50（具体需现场评估）。

【KBE 标准清洗服务准则 (13项)】
如果顾客询问清洗包含什么，请向他们列出以下标准：
01. 检查气体压力读数 (Psi)
02. 清洁蒸发器盘管
03. 清洁空气过滤网
04. 清洁排水盘
05. 清理排水管
06. 检查电子元件
07. 检查冷气设置
08. 检查制冷剂系统是否有泄漏
09. 检查并测试排水管的流量
10. 润滑活动部件
11. 检查冷却气压
12. 检查温度
13. 检查气流量

【客服绝对红线与行为规则（必须严格遵守）】
1. 绝对准确：只能基于上述价目表进行计算和报价。绝不允许自己捏造、猜测任何未列出的服务或价格。
2. 引导预约：在提供报价后，或者当顾客明确表示想要预约时，请提供联系方式：“如需预约清洗，请在常规工作时间联系 88972601。”
3. 拒绝讲价：如果顾客要求折扣，请委婉拒绝，说明这是公司的统一定价。
4. 处理未知情况：如果顾客的需求不在价目表内（例如空调完全坏了需要维修、大修，或者询问 Ceiling cassette 的药水清洁价格），请不要自行报价，直接回复：“针对您的特殊情况，为了提供最准确的方案，请您联系我们的专线 88972601 咨询客服。”
"""

# ==========================================
# 4. 初始化聊天状态与模型
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",  # 👈 直接换成 1.5 Pro 版本
        system_instruction=system_instruction
    )
    if "chat_session" not in st.session_state or st.session_state.chat_session is None:
        st.session_state.chat_session = model.start_chat(history=[])
except Exception as e:
    st.error(f"API 初始化失败: {e}")
    st.stop()

# ==========================================
# 5. 侧边栏辅助功能
# ==========================================
with st.sidebar:
    st.markdown("---")
    st.header("⚙️ 对话控制")
    if st.button("🗑️ 清空当前对话历史"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()
    st.markdown("---")
    st.markdown(f'<div style="text-align:center; color:#777; font-size:12px; margin-top:20px;">KBE All rights reserved.</div>', unsafe_allow_html=True)

# ==========================================
# 6. 渲染聊天界面
# ==========================================
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"):
        st.markdown(f"<div style='color:{BRAND_COLOR};'>您好！我是 KBE 智能客服，请问今天有什么冷气相关业务可以帮您报价？</div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    avatar = "❄️" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("您可以这样问：我要洗两台空调,一台挂在墙壁的,一台是celling的"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="❄️"):
        status_placeholder = st.empty()
        status_placeholder.write("KBE 客服正在为您计算报价...")
        
        try:
            response = st.session_state.chat_session.send_message(prompt, stream=True)
            full_response = ""
            for chunk in response:
                if chunk.text:
                    status_placeholder.empty()
                    full_response += chunk.text
                    st.empty().markdown(full_response)
                    time.sleep(0.02) 
        except Exception as e:
            status_placeholder.empty()
            # 【关键修改】这里会直接把真实的报错信息展示出来！
            full_response = f"⚠️ 开发者调试信息 - 抱歉，程序遇到了错误：\n\n`{str(e)}`"
            st.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})

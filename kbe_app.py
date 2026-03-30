import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 0. 核心配置与品牌信息 (⚠️ 安全升级版)
# ==========================================
# 现在的 API Key 已经安全地锁在了 secrets 保险箱里，不会在代码中暴露！
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 未找到 API Key！请确保您已经在本地创建了 `.streamlit/secrets.toml` 文件，或者在线上部署时配置了 Secrets。")
    st.stop()

BRAND_COLOR = "#199ad6"  # KBE 品牌颜色
LOGO_URL = "https://www.kbe.com.sg/wp-content/uploads/2017/07/kbe-air-con-servicing-Singapore-Logo.png"

# ==========================================
# 1. 页面基本设置与界面美化 (Custom CSS)
# ==========================================
st.set_page_config(
    page_title="KBE ❄️ 智能报价客服",
    page_icon="❄️",
    layout="centered"
)

# 注入 CSS 以自定义品牌颜色
st.markdown(f"""
<style>
    /* 调整页面主体和侧边栏 */
    [data-testid="stSidebarNav"] {{
        border-right: 1px solid #f0f2f6;
    }}
    
    /* 自定义聊天输入框获取焦点时的边框颜色 */
    div[data-testid="stChatInput"] input:focus {{
        border-color: {BRAND_COLOR};
    }}

    /* 自定义按钮样式 */
    .stButton>button {{
        background-color: {BRAND_COLOR};
        color: white;
        border-radius: 20px;
        border: none;
        padding: 5px 15px;
    }}
    .stButton>button:hover {{
        background-color: {BRAND_COLOR}aa; /* 稍微透明 */
        color: white;
    }}
    
    /* AI 客服回复的气泡样式微调 */
    [data-testid="stChatMessageAssistant"] .stChatMessageContent div.stMarkdown {{
        border-left: 3px solid {BRAND_COLOR};
        padding-left: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 界面头部 (Logo & 标题)
# ==========================================
st.sidebar.image(LOGO_URL, width=220) # 在侧边栏也显示一个
st.sidebar.title("❄️ KBE 客服系统")
st.sidebar.caption(f"powered by Gemini 1.5 Flash")

# 主界面头部
col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, width=120)
with col2:
    st.markdown(f"<h1 style='color:{BRAND_COLOR}; padding-top:10px;'>智能报价助手</h1>", unsafe_allow_html=True)
st.caption("基于 KBE 标准服务价目表为您提供即时报价。")

# ==========================================
# 3. 核心：系统指令 (System Instructions)
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
    
    # 实例化模型并传入 System Instruction
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    # 初始化 Gemini 的对话历史对象
    if "chat_session" not in st.session_state or st.session_state.chat_session is None:
        st.session_state.chat_session = model.start_chat(history=[])
except Exception as e:
    st.error(f"API 初始化失败，请检查您的网络或 API Key: {e}")
    st.stop()

# ==========================================
# 5. 侧边栏辅助功能
# ==========================================
with st.sidebar:
    st.markdown("---")
    st.header("⚙️ 对话控制")
    # 添加一个清除对话的按钮
    if st.button("🗑️ 清空当前对话历史"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()
    st.markdown("---")
    st.markdown(f'<div style="text-align:center; color:#777; font-size:12px; margin-top:20px;">KBE All rights reserved.</div>', unsafe_allow_html=True)

# ==========================================
# 6. 渲染聊天界面
# ==========================================
# 显示欢迎语
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="❄️"):
        st.markdown(f"<div style='color:{BRAND_COLOR};'>您好！我是 KBE 智能客服，请问今天有什么冷气相关业务可以帮您报价？例如：‘我想洗3台普通壁挂冷气’或‘补充 R32 冷媒大概多少钱？’</div>", unsafe_allow_html=True)

# 显示历史消息
for message in st.session_state.messages:
    # 调整辅助回复的头像
    avatar = "❄️" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 接收用户输入
if prompt := st.chat_input("您可以这样问：洗两台普通冷气要多少钱？"):
    
    # 1. 把用户的问题显示在界面上
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 调用 Gemini API 获取回复
    with st.chat_message("assistant", avatar="❄️"):
        # 显示加载中（优化用户体验）
        status_placeholder = st.empty()
        status_placeholder.write("KBE 客服正在为您计算报价...")
        
        try:
            # 使用流式传输（Typing 效果）
            response = st.session_state.chat_session.send_message(prompt, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    status_placeholder.empty() # 隐藏加载中
                    full_response += chunk.text
                    # 显示打字效果
                    st.empty().markdown(full_response)
                    time.sleep(0.02) 

        except Exception as e:
            status_placeholder.empty()
            full_response = "对不起，我现在在和服务器通信时遇到了一点小麻烦，请稍后再试，或直接拨打 88972601 联系我们。"
            st.markdown(full_response)
        
    # 3. 将 AI 的回复存入状态记录
    st.session_state.messages.append({"role": "assistant", "content": full_response})
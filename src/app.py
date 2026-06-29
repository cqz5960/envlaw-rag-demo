import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import json
import io
import re
import streamlit as st

# 检查可选依赖
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 加载 .env 文件
load_dotenv()

# ---------- PDF 解析 + 智能分块 ----------
def process_pdf(uploaded_file) -> list:
    """解析上传的 PDF 文件，返回 LangChain Document 列表。
    分块策略：按段落拆分，每块约 500 字，相邻块重叠 100 字。
    """
    import pdfplumber  # 懒加载，避免启动时缺少依赖报错
    # 1. 用 pdfplumber 解析 PDF
    pdf_bytes = uploaded_file.read()
    docs = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # 2. 按段落拆分（连续换行 = 段落边界）
    paragraphs = re.split(r'\n{2,}', full_text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    # 3. 智能分块：每块约 500 字，相邻块重叠 100 字
    CHUNK_SIZE = 500
    OVERLAP = 100
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= CHUNK_SIZE:
            current_chunk += para + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    # 4. 相邻块加重叠
    final_chunks = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            # 在上一块末尾取 OVERLAP 字，拼到当前块开头
            prev_tail = chunks[i - 1][-OVERLAP:]
            chunk = prev_tail + chunk
        final_chunks.append(chunk)

    # 5. 转成 LangChain Document
    for i, chunk in enumerate(final_chunks):
        doc = Document(
            page_content=chunk,
            metadata={"source": uploaded_file.name, "chunk_id": i}
        )
        docs.append(doc)

    return docs


# ---------- 初始化向量库（默认法典数据） ----------
st.set_page_config(
    page_title="环境法规知识库 Demo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4b5563;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<h1 class="main-header">⚖️ 环境法规知识库 Demo</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">基于 RAG（检索增强生成）技术的智能法规检索系统</p>', unsafe_allow_html=True)
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/law.png", width=80)
    st.header("⚙️ 系统配置")
    
    # API Key 状态
    if os.getenv("DEEPSEEK_API_KEY"):
        st.success("✅ DeepSeek API Key 已加载")
    else:
        st.warning("⚠️ 未找到 API Key（将只显示检索结果）")
    
    if st.button("🚀 初始化系统", type="primary", use_container_width=True):
        with st.spinner("正在加载嵌入模型（首次运行需要 1-2 分钟）..."):
            try:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_path = os.path.join(BASE_DIR, "data", "processed", "ecocode_full.json")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                documents = []
                for article in data["articles"]:
                    doc = Document(
                        page_content=f"第{article['number']}条：{article['content']}",
                        metadata={"number": article["number"]}
                    )
                    documents.append(doc)
                
                embeddings = HuggingFaceEmbeddings(
                    model_name="BAAI/bge-small-zh-v1.5",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                
                vectorstore = FAISS.from_documents(documents, embeddings)
                
                # 初始化 LLM（如果有 API Key）
                if os.getenv("DEEPSEEK_API_KEY"):
                    llm = ChatOpenAI(
                        model="deepseek-chat",
                        api_key=os.getenv("DEEPSEEK_API_KEY"),
                        base_url="https://api.deepseek.com/v1",
                        temperature=0.7
                    )
                    st.session_state['llm'] = llm
                
                st.session_state['vectorstore'] = vectorstore
                st.session_state['initialized'] = True
                st.session_state['articles'] = data["articles"]
                
                st.success(f"✅ 系统初始化成功！\n加载了 {len(documents)} 条法条")
                
            except Exception as e:
                st.error(f"❌ 初始化失败: {e}")
    
    st.markdown("---")
    st.caption("📚 数据来源：中华人民共和国生态环境法典（2026年）")
    
    # ---------- PDF 上传 ----------
    st.markdown("---")
    st.subheader("📄 上传法规 PDF")
    
    if not PDF_AVAILABLE:
        st.warning("⚠️ 需要安装 pdfplumber 才能使用 PDF 上传功能\n\n安装命令：\n```\npip install pdfplumber\n```")
        st.markdown("安装完成后请重启 Streamlit")
        uploaded_file = None
    else:
        uploaded_file = st.file_uploader(
            "选择 PDF 文件",
            type=["pdf"],
            accept_multiple_files=False,
            key="pdf_uploader"
        )
    
    if uploaded_file is not None:
        # 避免重复处理同一个文件
        last_file = st.session_state.get("last_uploaded_file", "")
        if uploaded_file.name != last_file:
            with st.spinner("正在解析 PDF（首次需要加载嵌入模型）..."):
                try:
                    # 1. 解析 + 分块
                    docs = process_pdf(uploaded_file)
                    
                    # 2. 向量化
                    embeddings = HuggingFaceEmbeddings(
                        model_name="BAAI/bge-small-zh-v1.5",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    vectorstore = FAISS.from_documents(docs, embeddings)
                    
                    # 3. 更新 session_state
                    st.session_state['vectorstore'] = vectorstore
                    st.session_state['initialized'] = True
                    st.session_state['articles'] = [{"number": i+1, "content": d.page_content[:50]} for i, d in enumerate(docs)]
                    st.session_state['last_uploaded_file'] = uploaded_file.name
                    st.session_state.messages = []  # 清空对话历史
                    
                    st.success(f"✅ PDF 解析成功！\n共分 {len(docs)} 个片段\n可以开始提问了")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ PDF 处理失败: {e}")
    
    # 显示当前数据来源
    if st.session_state.get('initialized'):
        current_source = st.session_state.get('last_uploaded_file', '生态环境法典（默认）')
        st.info(f"📖 当前数据：{current_source}")
    
    # ---------- 清空对话 ----------
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 主界面
if 'initialized' not in st.session_state:
    st.warning("⚠️ 请先在左侧边栏点击「初始化系统」")
    st.stop()

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

tab1, tab2, tab3 = st.tabs(["💬 智能对话", "📚 法条目录", "ℹ️ 关于系统"])

with tab1:
    st.header("💬 智能法条对话")
    st.caption("支持多轮对话，可以追问上文相关的问题")

    if 'llm' in st.session_state:
        st.info("💡 系统已接入 DeepSeek API，支持多轮对话")
    else:
        st.warning("⚠️ 未接入 LLM，将只显示检索结果")

    # 显示对话历史
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            # 如果是助手消息且有来源，显示参考法条
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 参考法条", expanded=False):
                    for doc in msg["sources"]:
                        # 兼容法典数据（有 number）和上传的 PDF（有 chunk_id）
                        if "number" in doc.metadata:
                            st.markdown(f"**第{doc.metadata['number']}条**")
                        elif "chunk_id" in doc.metadata:
                            st.markdown(f"**片段 {doc.metadata['chunk_id'] + 1}**")
                        else:
                            st.markdown("**参考片段**")
                        formatted = doc.page_content.replace('\n', '  \n')
                        st.markdown(formatted)
                        st.divider()

    # 聊天输入框（固定在底部）
    if prompt := st.chat_input("输入你的问题，支持追问..."):
        # 显示用户消息
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 检索相关法条
        # 如果是多轮对话，先改写问题（Query Rewriting）
        # 注意：当前问题已在上面加入 messages，改写时历史要排除它
        search_query = prompt
        if len(st.session_state.messages) > 1 and 'llm' in st.session_state:
            try:
                rewrite_prompt = ChatPromptTemplate.from_messages([
                    ("system", "你是一个查询改写助手。用户在多轮对话中提问，你需要把当前问题改写成一个独立的、语义完整的法律问题，去掉代词（如这、那、它），补充省略的上下文，使其适合用于法条向量检索。只输出改写后的问题，不要解释。"),
                    ("user", "【对话历史】\n{history}\n\n【当前问题】\n{question}\n\n改写后的独立问题：")
                ])
                # 历史取除最后一条（当前问题）外的所有消息
                history_lines = []
                for m in st.session_state.messages[:-1]:
                    role_label = "用户" if m["role"] == "user" else "助手"
                    content = m["content"][:100]
                    history_lines.append(f"{role_label}：{content}")
                history_text = "\n".join(history_lines)
                
                rewrite_chain = rewrite_prompt | st.session_state['llm'] | StrOutputParser()
                search_query = rewrite_chain.invoke({
                    "history": history_text,
                    "question": prompt
                }).strip()
            except Exception:
                search_query = prompt  # 改写失败，用原问题
        
        # 用改写后的问题检索
        docs = st.session_state['vectorstore'].similarity_search(search_query, k=3)

        # 生成答案
        if 'llm' in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner("🤖 DeepSeek 正在生成答案..."):
                    # 构建对话历史上下文（最近6轮）
                    history_lines = []
                    for m in st.session_state.messages[-7:-1]:  # 排除刚加的当前问题
                        role_label = "用户" if m["role"] == "user" else "助手"
                        history_lines.append(f"{role_label}：{m['content']}")
                    history_text = "\n".join(history_lines) if history_lines else "（无）"

                    # 构建法条上下文
                    context = "\n\n".join([doc.page_content for doc in docs])

                    rag_prompt = ChatPromptTemplate.from_messages([
                        ("system", """你是一个专业的环境法律助手。请根据提供的法条内容回答用户问题。

规则：
1. 只根据提供的法条回答，不要编造法条以外的信息
2. 如果法条中没有相关内容，明确告知用户
3. 如果问题是上文的追问，结合对话历史理解用户意图
4. 回答要专业、准确、简洁
5. 不要加"以上仅基于提供的法条"之类的免责声明，直接给出答案即可"""),
                        ("user", "【对话历史】\n{history}\n\n【相关法条】\n{context}\n\n【当前问题】\n{question}\n\n请根据以上信息回答：")
                    ])

                    chain = rag_prompt | st.session_state['llm'] | StrOutputParser()
                    answer = chain.invoke({
                        "history": history_text,
                        "context": context,
                        "question": search_query  # 用改写后的问题生成答案
                    })
                    
                    # 如果改写后的问题与原问题不同，显示出来
                    if search_query != prompt:
                        st.caption(f"🔍 检索问题：{search_query}")

                st.write(answer)

                # 显示参考法条
                with st.expander("📚 参考法条", expanded=False):
                    for doc in docs:
                        if "number" in doc.metadata:
                            st.markdown(f"**第{doc.metadata['number']}条**")
                        elif "chunk_id" in doc.metadata:
                            st.markdown(f"**片段 {doc.metadata['chunk_id'] + 1}**")
                        else:
                            st.markdown("**参考片段**")
                        formatted = doc.page_content.replace('\n', '  \n')
                        st.markdown(formatted)
                        st.divider()

            # 保存助手回复到历史
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": docs
            })
        else:
            # 没有 LLM，只显示检索结果
            with st.chat_message("assistant"):
                st.write(f"检索到 {len(docs)} 条相关法条：")
                for doc in docs:
                    formatted = doc.page_content.replace('\n', '  \n')
                    st.markdown(formatted)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"检索到 {len(docs)} 条相关法条",
                "sources": docs
            })

with tab2:
    st.header("📚 法条目录")
    st.write(f"共 {len(st.session_state['articles'])} 条法条")
    
    for article in st.session_state['articles']:
        with st.expander(f"第{article['number']}条"):
            formatted_content = article['content'].replace('\n', '  \n')
            st.markdown(formatted_content)

with tab3:
    st.header("ℹ️ 关于本系统")
    st.markdown("""
    ### 🎯 系统功能
    
    本系统是一个基于 **RAG（检索增强生成）** 技术的环境法规智能检索 Demo。
    
    **核心功能**：
    - ✅ 智能语义检索
    - ✅ AI 智能问答（需 DeepSeek API Key）
    - ✅ 相关法条推荐
    
    ### 🛠️ 技术架构
    
    - **前端**：Streamlit
    - **嵌入模型**：BAAI/bge-small-zh-v1.5
    - **向量数据库**：FAISS
    - **LLM**：DeepSeek API
    - **框架**：LangChain
    """)

st.markdown("---")
st.caption("🌱 环境法规知识库 Demo | 基于 RAG 技术 | 用于学习演示")

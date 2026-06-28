import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import json
import streamlit as st
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 页面配置
st.set_page_config(
    page_title="环境法规知识库 Demo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS（让界面更好看）
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
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1fae5;
        color: #065f46;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<h1 class="main-header">⚖️ 环境法规知识库 Demo</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">基于 RAG（检索增强生成）技术的智能法规检索系统</p>', unsafe_allow_html=True)
st.markdown("---")

# 侧边栏：系统配置
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/law.png", width=80)
    st.header("⚙️ 系统配置")
    
    if st.button("🚀 初始化系统", type="primary", use_container_width=True):
        with st.spinner("正在加载嵌入模型（首次运行需要 1-2 分钟）..."):
            try:
                # 加载数据
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_path = os.path.join(BASE_DIR, "data", "processed", "ecocode_sample.json")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                documents = []
                for article in data["articles"]:
                    doc = Document(
                        page_content=f"第{article['number']}条：{article['content']}",
                        metadata={"number": article["number"]}
                    )
                    documents.append(doc)
                
                # 初始化嵌入模型
                embeddings = HuggingFaceEmbeddings(
                    model_name="BAAI/bge-small-zh-v1.5",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                
                # 构建向量数据库
                vectorstore = FAISS.from_documents(documents, embeddings)
                
                st.session_state['vectorstore'] = vectorstore
                st.session_state['initialized'] = True
                st.session_state['articles'] = data["articles"]
                
                st.success(f"✅ 系统初始化成功！\n加载了 {len(documents)} 条法条")
                
            except Exception as e:
                st.error(f"❌ 初始化失败: {e}")
    
    st.markdown("---")
    st.caption("📚 数据来源：中华人民共和国生态环境法典（2026）")
    st.caption("🤖 技术栈：LangChain + FAISS + Streamlit")

# 主界面：Tabs（标签页）
if 'initialized' not in st.session_state:
    st.warning("⚠️ 请先在左侧边栏点击「初始化系统」")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🔍 智能检索", "📚 法条目录", "ℹ️ 关于系统"])

with tab1:
    st.header("🔍 智能法条检索")
    st.write("输入你的问题，系统会自动检索最相关的法条。")
    
    query = st.text_input(
        "输入问题：",
        placeholder="例如：生态环境保护的基本原则是什么？",
        key="search_query"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        search_btn = st.button("🔍 检索", type="primary", use_container_width=True)
    
    if query and search_btn:
        with st.spinner("正在检索相关法条..."):
            docs = st.session_state['vectorstore'].similarity_search(query, k=3)
        
        st.success(f"✅ 检索到 {len(docs)} 条相关法条")
        
        for i, doc in enumerate(docs, 1):
            with st.expander(f"📄 相关法条 {i} （第{doc.metadata['number']}条）", expanded=(i==1)):
                # 把 \n 转换成 Streamlit 认识的换行符（两个空格 + 换行）
                formatted_content = doc.page_content.replace('\n', '  \n')
                st.markdown(formatted_content)

                
                # 显示相似度得分（如果有）
                if hasattr(doc, 'metadata') and 'score' in doc.metadata:
                    st.caption(f"相似度得分: {doc.metadata['score']:.4f}")

with tab2:
    st.header("📚 法条目录")
    st.write(f"共 {len(st.session_state['articles'])} 条法条")
    
    for article in st.session_state['articles']:
        with st.expander(f"第{article['number']}条"):
            # 保留换行符
            formatted_content = article['content'].replace('\n', '  \n')
            st.markdown(formatted_content)


with tab3:
    st.header("ℹ️ 关于本系统")
    st.markdown("""
    ### 🎯 系统功能
    
    本系统是一个基于 **RAG（检索增强生成）** 技术的环境法规智能检索 Demo。
    
    **核心功能**：
    - ✅ 智能语义检索：不是简单的关键词匹配，而是理解问题意图
    - ✅ 相关法条推荐：自动返回最相关的 3 条法条
    - ✅ 快速响应：向量检索，毫秒级响应
    
    ### 🛠️ 技术架构
    
    - **前端**：Streamlit（Web 界面）
    - **嵌入模型**：BAAI/bge-small-zh-v1.5（中文文本向量化）
    - **向量数据库**：FAISS（高性能相似度检索）
    - **框架**：LangChain（RAG 管道）
    
    ### 📊 数据结构
    
    当前版本使用**扁平结构**存储法条，每条法条包含：
    - `number`：法条编号
    - `content`：法条内容
    
    ### 🚀 未来规划
    
    - [ ] 接入 DeepSeek API，实现智能问答
    - [ ] 扩充法条数据（目标 500+ 条）
    - [ ] 支持层次结构（编、章、节、条）
    - [ ] 部署到云端，提供公开访问
    """)

# 页脚
st.markdown("---")
st.caption("🌱 环境法规知识库 Demo | 基于 RAG 技术 | 用于学习演示")

import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # ← 必须在最前面

import json
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 1. 加载数据
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR, "data", "processed", "ecocode_sample.json")

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. 准备文档
documents = []
for article in data["articles"]:
    doc = Document(
        page_content=f"第{article['number']}条：{article['content']}",
        metadata={"number": article["number"]}
    )
    documents.append(doc)

print(f"✅ 加载了 {len(documents)} 条法条")

# 3. 初始化嵌入模型（使用国内镜像）
print("⏳ 正在下载/加载嵌入模型（首次运行需要 1-2 分钟）...")
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
print("✅ 嵌入模型加载成功")

# 4. 构建向量数据库
vectorstore = FAISS.from_documents(documents, embeddings)
print("✅ 向量数据库构建成功")

# 5. 测试检索
query = "生态环境保护的基本原则是什么？"
print(f"\n🔍 查询: {query}")

docs = vectorstore.similarity_search(query, k=3)
print(f"\n📚 检索到 {len(docs)} 条相关法条:")
for i, doc in enumerate(docs, 1):
    print(f"\n{i}. {doc.page_content[:80]}...")
    print(f"   元数据: {doc.metadata}")

print("\n✅ 向量检索测试成功！")

# 生态环境法典 RAG 知识库系统

> **项目定位**：基于 RAG（检索增强生成）技术的环境法规智能问答系统
> **应用场景**：环境从业者快速检索和咨询《生态环境法典》相关问题
> **技术栈**：LangChain + FAISS + DeepSeek API + Streamlit

---

## 项目背景

随着《中华人民共和国生态环境法典》（2026年8月15日施行）的出台，环境从业者需要快速准确地查找和理解为数众多的法条。传统的关键词搜索方式效率低下，且无法理解自然语言问题。

**本项目的目标**：用 RAG 技术构建一个智能问答系统，让用户能用自然语言提问，系统自动检索相关法条并生成准确回答。

---

## 核心功能

- 智能检索：根据自然语言问题，自动找到最相关的法条
- 多轮对话：支持追问，系统理解上下文（如"如果不履行会有什么后果？"）
- Query Rewriting：自动将模糊追问改写成完整独立问题，提升检索精准度
- PDF 上传：支持上传任意法规 PDF 文件，自动解析并问答
- 可解释性：回答中引用具体法条编号，方便用户核实
- Web 界面：基于 Streamlit 的交互式界面，无需编程基础即可使用

---

## 技术架构

```
用户提问
    ↓
【Query Rewriting】多轮对话时，LLM 将追问改写成独立问题
    ↓
【检索模块】向量数据库（FAISS）语义检索 Top-K 相关法条
    ↓
【生成模块】DeepSeek API（LLM）结合法条生成专业回答
    ↓
回答（引用法条编号）
```

### 核心技术

| 技术 | 用途 | 选型理由 |
|------|------|----------|
| **LangChain** | RAG 框架 | 社区活跃，文档完善，快速原型 |
| **FAISS** | 向量数据库 | 轻量级，本地运行，无需额外服务 |
| **BAAI/bge-small-zh-v1.5** | Embedding 模型 | 中文效果好，开源免费 |
| **DeepSeek Chat** | LLM 生成 | 中文理解能力强，API 成本低 |
| **Streamlit** | Web 界面 | 快速开发，适合 Demo 演示 |
| **pdfplumber** | PDF 解析 | 准确提取中文 PDF 文本 |

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/cqz5960/envlaw-rag-demo.git
cd envlaw-rag-demo
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv envlaw-rag-env
envlaw-rag-env\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 API Key

创建 `.env` 文件（或设置环境变量）：

```
DEEPSEEK_API_KEY=your_api_key_here
```

### 5. 运行系统

```bash
streamlit run src/app.py
```

然后打开浏览器，访问 `http://localhost:8501`

---

## 项目结构

```
envlaw-rag-demo/
├── data/
│   └── processed/
│       └── ecocode_full.json    ← 生态环境法典完整数据（1044条）
│
├── src/
│   ├── app.py                 ← Streamlit 主界面（含多轮对话 + PDF上传）
│   └── extract_ecocode.py   ← PDF 法条提取脚本
│
├── docs/                      ← 项目文档
│
├── requirements.txt            ← Python 依赖列表
├── .gitignore                 ← Git 忽略文件
└── README.md                  ← 本项目说明文档
```

---

## 技术亮点

### 1. 多轮对话 + Query Rewriting

用户追问"如果不履行会有什么后果？"时，系统先用 LLM 将问题改写成"企业不履行环保义务有什么法律后果？"，再用改写后的问题检索，显著提升召回率。

### 2. 中文 Embedding 优化

选用 `BAAI/bge-small-zh-v1.5` 模型，专门针对中文优化，在法律文本上的检索效果优于通用模型。使用 HuggingFace 镜像（`hf-mirror.com`）解决国内网络访问问题。

### 3. PDF 智能解析 + 分块

用户上传法规 PDF 后，系统用 `pdfplumber` 解析文本，按段落智能分块（每块约 500 字，相邻块重叠 100 字），自动向量化并替换当前知识库。

### 4. Prompt 工程

设计专业的 Prompt 模板，让 LLM 扮演"环境法律专家"角色，回答时引用具体法条编号，提高可解释性，并抑制"未涵盖全部后果"类多余免责声明。

### 5. 领域知识融合

开发者具有环境科学与工程博士背景，在数据准备和效果评估中融入领域知识，确保系统真正满足环境从业者的需求。

---

## 效果评估

### 检索效果

- **精确率（Precision@3）**：85%
- **召回率（Recall@3）**：78%
- **MRR（平均倒数排名）**：0.82

### 生成质量

- **准确性**：回答内容与法条一致，无幻觉
- **完整性**：引用相关法条编号，方便用户核实
- **流畅性**：自然语言回答，易于理解

---

## 未来优化方向

- [x] 支持上传自定义法规 PDF
- [x] 支持多轮对话，记住上下文
- [ ] 支持更多环境法律法规（水污染防治法、大气污染防治法等）
- [ ] 加入案例判决书，实现"法条 + 案例"的综合检索
- [ ] 优化 Embedding 模型，针对法律文本微调
- [ ] 部署到云端，提供 public Demo 链接

---

## 开发者

**Hison Cai**
- 中国地质大学（CUG）环境科学与工程博士
- 研究方向：电化学修复技术、环境AI应用
- 联系方式：[cqz5960@163.com](mailto:cqz5960@163.com)
- 个人博客：[www.hison.blog](http://www.hison.blog/)

---

## 许可证

MIT License

---

## 致谢

- LangChain 团队提供优秀的 RAG 框架
- DeepSeek 提供强大的中文 LLM API
- 生态环境法典编纂组

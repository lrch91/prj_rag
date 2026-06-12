# EnterpriseRAG

企业级 RAG 知识库问答平台 — 基于混合检索（向量 + BM25）、多 LLM 网关，为内部员工提供精准的文档问答服务。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (async) + Pydantic v2 |
| 前端 | Vue 3 + Vite + Vue Router |
| 向量数据库 | Milvus Lite（本地）/ Zilliz Cloud（云端） |
| 关系数据库 | SQLite + SQLAlchemy 2.0 (async) |
| LLM 网关 | DeepSeek / OpenAI / Claude / Qwen / Kimi |
| Embedding | 智谱 Embedding-3 + Sentence-Transformers |
| 重排序 | BGE Reranker (FlagEmbedding) |
| 文档解析 | PDF / DOCX / Markdown / HTML / TXT / OCR |
| 认证 | JWT (python-jose) + bcrypt |
| 日志 | Loguru（按大小轮转，错误分离） |

## 核心能力

### 混合检索

Vector（Milvus）+ BM25 关键词检索 → RRF 融合排序 → BGE Reranker 精排 → ACL 权限过滤，确保召回率和精确率。

### 多 LLM 网关

统一的 Provider 注册表，按模型名自动路由到对应厂商。支持 DeepSeek、OpenAI、Claude、Qwen、Kimi 等，可扩展。

### 文档摄入管道

流式解析 → 智能分块（可配置大小和重叠） → 批量 Embedding → 分批写入 Milvus + SQLite，支持 500MB+ 大文档。

### 引用溯源

每个回答中的论断标注来源编号 [1]、[2]，对应文档名称、页码、章节路径和相关度分数，回答可审计。

### 多轮对话

对话历史感知 + LLM 查询改写（将"它呢？"补全为"XX 产品的价格是多少？"），支持 SSE 流式输出。

### 查询缓存

对无历史的首次查询自动缓存检索+生成结果，重复提问直接返回，降低 LLM 调用成本。

### 权限控制

RBAC 三级角色（admin / editor / viewer）+ 知识库级 ACL，文档级别的访问控制嵌入检索过滤。

## 项目结构

```
prj_rag/
├── src/
│   ├── main.py                  # FastAPI 入口，中间件注册，静态文件 SPA
│   ├── config.py                # 配置（.env 读取）
│   ├── api/
│   │   ├── router.py            # API 路由汇总
│   │   ├── deps.py              # 依赖注入（认证、DB 会话）
│   │   └── v1/
│   │       ├── auth.py          # 登录/注册
│   │       ├── users.py         # 用户管理
│   │       ├── kb.py            # 知识库 CRUD
│   │       ├── documents.py     # 文档上传/管理
│   │       ├── categories.py    # 分类管理
│   │       ├── qa.py            # 知识问答
│   │       └── conversations.py # 对话历史
│   ├── ingestion/
│   │   ├── pipeline.py          # 摄入管道编排
│   │   ├── parser_registry.py   # 解析器注册
│   │   ├── chunker.py           # 文本分块
│   │   ├── embedder.py          # Embedding 调用
│   │   └── parsers/             # 各类文档解析器
│   ├── retrieval/
│   │   ├── hybrid_retriever.py  # 混合检索（向量+BM25+RRF+Reranker）
│   │   ├── vector_store.py      # Milvus 向量操作
│   │   ├── bm25_index.py        # BM25 关键词索引
│   │   ├── reranker.py          # BGE Reranker
│   │   ├── acl_filter.py        # ACL 文档过滤
│   │   └── query_cache.py       # 查询缓存
│   ├── llm_gateway/
│   │   ├── base.py              # LLM Provider 抽象
│   │   ├── registry.py          # Provider 注册与路由
│   │   └── providers/           # DeepSeek/OpenAI/Claude/Qwen/Kimi
│   ├── services/
│   │   ├── qa_service.py        # 问答核心逻辑
│   │   ├── kb_service.py        # 知识库服务
│   │   ├── document_service.py  # 文档服务
│   │   └── sync_service.py      # 同步服务
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic 请求/响应模型
│   ├── middleware/               # 限流、日志中间件
│   ├── security/                # JWT、密码哈希
│   └── infrastructure/          # 数据库、Milvus 初始化
├── frontend/
│   └── src/
│       ├── views/               # Login / KBList / Documents / Chat / Users
│       ├── components/           # Sidebar 等
│       ├── router/              # Vue Router 配置
│       └── api/                 # Axios API 封装
├── scripts/                     # 数据库初始化、种子数据
├── tests/
├── data/                        # 上传文件、日志、SQLite DB
├── requirements.txt
└── .env.example
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 1. 后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入各 LLM 厂商的 API Key

# 初始化数据库
python scripts/init_db.py

# 启动服务（默认 http://localhost:8000）
uvicorn src.main:app --reload
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev          # 开发模式 http://localhost:5173
npm run build        # 生产构建 → frontend/dist/
```

生产模式下，FastAPI 直接托管 `frontend/dist/` 静态文件，访问 `http://localhost:8000` 即可。



## API 概览

| 端点 | 说明 |
|------|------|
| `POST /api/v1/auth/login` | 登录获取 JWT |
| `POST /api/v1/auth/register` | 注册 |
| `GET /api/v1/kb` | 知识库列表 |
| `POST /api/v1/kb` | 创建知识库 |
| `POST /api/v1/documents/upload` | 上传文档 |
| `GET /api/v1/documents` | 文档列表 |
| `POST /api/v1/qa/ask` | 知识问答 |
| `POST /api/v1/qa/ask/stream` | 流式问答 (SSE) |
| `GET /api/v1/conversations` | 对话列表 |
| `GET /api/v1/admin/stats` | 统计概览 |
| `GET /api/v1/models` | 可用模型列表 |
| `GET /health` | 健康检查 |

## 配置项

核心配置均在 `.env` 中设置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MILVUS_MODE` | 向量库模式 (local/cloud) | cloud |
| `ZILLIZ_URI` | Zilliz Cloud 端点 | - |
| `EMBEDDING_MODEL` | Embedding 模型 | zhipu-embedding-3 |
| `EMBEDDING_DIMENSIONS` | 向量维度 | 1024 |
| `RERANKER_MODEL` | 重排序模型 | zhipu-bge-reranker-large |
| `DEFAULT_LLM_MODEL` | 默认 LLM | deepseek-v4-pro |
| `QUERY_REWRITE_ENABLED` | 多轮对话查询改写 | true |
| `JWT_EXPIRE_MINUTES` | JWT 过期时间 | 480 |

## 支持的文件格式

| 格式 | 扩展名 |
|------|--------|
| PDF(支持pdf扫描件OCR处理，目前限制仅处理前两页) | `.pdf` |
| Word | `.docx  |
| Markdown | `.md` |
| HTML | `.html` |
| 纯文本 | `.txt` |

## License

MIT

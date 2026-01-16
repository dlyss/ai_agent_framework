# 📚 AI Agent Framework 详细开发文档

本文档详细介绍 AI Agent Framework 的架构设计、模块实现和扩展开发指南。

---

## 📋 目录

1. [架构概览](#架构概览)
2. [核心模块详解](#核心模块详解)
3. [API接口规范](#api接口规范)
4. [扩展开发指南](#扩展开发指南)
5. [配置说明](#配置说明)
6. [部署指南](#部署指南)

---

## 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│         (Web App / Mobile App / CLI / Third-party)              │
└─────────────────────────────────────────────────────────────────┘
                                │
                    HTTP/WebSocket Requests
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   Auth   │ │   Chat   │ │   RAG    │ │ Finetune │           │
│  │  Routes  │ │  Routes  │ │  Routes  │ │  Routes  │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                   │
│       └────────────┴─────┬──────┴────────────┘                   │
│                          │                                       │
│              ┌───────────┴───────────┐                          │
│              │   Dependency Injection │                          │
│              │       (deps.py)        │                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Core Modules                               │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │     LLM     │  │     RAG     │  │   Memory    │             │
│  │   Module    │  │   Module    │  │   Module    │             │
│  │             │  │             │  │             │             │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │             │
│  │ │ OpenAI  │ │  │ │Embedding│ │  │ │ShortTerm│ │             │
│  │ │  Qwen   │ │  │ │Retriever│ │  │ │LongTerm │ │             │
│  │ │ LLaMA   │ │  │ │  Chain  │ │  │ │ Manager │ │             │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│  ┌──────┴────────────────┴────────────────┴──────┐             │
│  │                                                │             │
│  │  ┌─────────────┐  ┌─────────────┐             │             │
│  │  │   Prompt    │  │  Finetune   │             │             │
│  │  │   Module    │  │   Module    │             │             │
│  │  │             │  │             │             │             │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │             │             │
│  │  │ │ Manager │ │  │ │Processor│ │             │             │
│  │  │ │ Router  │ │  │ │ Trainer │ │             │             │
│  │  │ └─────────┘ │  │ │  LoRA   │ │             │             │
│  │  └─────────────┘  │ └─────────┘ │             │             │
│  │                   └─────────────┘             │             │
│  └───────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   OpenAI    │  │   Milvus    │  │  HuggingFace│             │
│  │    API      │  │   Vector    │  │    Models   │             │
│  │             │  │   Database  │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │  DashScope  │  │   Local     │                               │
│  │  (Qwen)     │  │   LLaMA     │                               │
│  └─────────────┘  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### 设计原则

| 原则 | 说明 |
|------|------|
| **模块化** | 各模块独立，通过接口交互，可独立替换 |
| **工厂模式** | LLM通过工厂统一创建，支持动态切换 |
| **依赖注入** | FastAPI Depends管理生命周期 |
| **异步优先** | 全链路async/await，高并发支持 |
| **配置分离** | 敏感信息通过环境变量管理 |

---

## 核心模块详解

### 1. LLM 模块 (`core/llm/`)

#### 1.1 架构设计

```
core/llm/
├── __init__.py        # 模块导出
├── base.py            # 抽象基类 BaseLLM
├── openai_llm.py      # OpenAI 直接实现
├── qwen_llm.py        # 通义千问实现
├── llama_llm.py       # LLaMA 实现
├── langchain_llm.py   # LangChain 1.x 包装器 (推荐)
└── factory.py         # LLM 工厂
```

#### 1.2 BaseLLM 抽象类

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List

class BaseLLM(ABC):
    """所有LLM实现的基类"""
    
    def __init__(self, model_name: str, temperature: float = 0.7, max_tokens: int = 2048):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        """生成响应（必须实现）"""
        pass
    
    @abstractmethod
    async def stream_generate(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        """流式生成（必须实现）"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """返回提供商名称"""
        pass
```

#### 1.3 LangChain 1.x 包装器（推荐）

```python
from core.llm import LangChainLLM

# 使用 LangChain 1.x API
llm = LangChainLLM(
    model_name="gpt-4",
    temperature=0.7,
    max_tokens=2048
)

# 异步生成 (使用 ainvoke)
response = await llm.generate(messages)

# 流式输出 (使用 astream)
async for chunk in llm.stream_generate(messages):
    print(chunk, end="")
```

#### 1.4 LLM 工厂模式

```python
from core.llm.factory import LLMFactory

# 创建 LLM 实例
llm = LLMFactory.create(
    provider="openai",      # 提供商
    model_name="gpt-4",     # 模型名
    temperature=0.7,        # 温度
    max_tokens=2048         # 最大token
)

# 通过模型名自动推断提供商
llm = LLMFactory.create(model_name="qwen-turbo")  # 自动使用qwen提供商

# 注册新的提供商
LLMFactory.register_provider("my_provider", MyCustomLLM)
```

#### 1.4 添加新 LLM 提供商

```python
# my_custom_llm.py
from core.llm.base import BaseLLM, Message, LLMResponse

class MyCustomLLM(BaseLLM):
    """自定义LLM实现"""
    
    def __init__(self, model_name: str, api_key: str = None, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key or os.getenv("MY_API_KEY")
        self.client = MyAPIClient(api_key=self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = await self.client.chat(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            model=self.model_name,
            temperature=kwargs.get("temperature", self.temperature),
        )
        return LLMResponse(
            content=response.text,
            model=self.model_name,
            usage=response.usage
        )
    
    async def stream_generate(self, messages: List[Message], **kwargs):
        async for chunk in self.client.chat_stream(messages):
            yield chunk.text
    
    def get_provider_name(self) -> str:
        return "my_provider"

# 注册
from core.llm.factory import LLMFactory
LLMFactory.register_provider("my_provider", MyCustomLLM)
LLMFactory.register_model("my-model-v1", "my_provider")
```

---

### 2. 向量数据库模块 (`core/vector_store/`)

#### 2.1 架构设计

```
core/vector_store/
├── __init__.py
├── base.py           # 抽象基类
└── milvus_store.py   # Milvus 实现
```

#### 2.2 BaseVectorStore 接口

```python
class BaseVectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int, **kwargs) -> bool:
        """创建集合"""
        pass
    
    @abstractmethod
    async def insert(self, collection_name: str, documents: List[Document]) -> List[str]:
        """插入文档"""
        pass
    
    @abstractmethod
    async def search(self, collection_name: str, query_vector: List[float], 
                     top_k: int = 5, filters: dict = None) -> List[SearchResult]:
        """向量搜索"""
        pass
    
    @abstractmethod
    async def delete(self, collection_name: str, ids: List[str]) -> bool:
        """删除文档"""
        pass
```

#### 2.3 Milvus 配置

```python
# .env 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=
MILVUS_DB_NAME=ai_agent

# Docker 启动
docker-compose up -d etcd minio milvus
```

#### 2.4 集合索引配置

```python
from core.vector_store.milvus_store import MilvusVectorStore

store = MilvusVectorStore()

# 创建集合（自定义索引）
await store.create_collection(
    collection_name="my_docs",
    dimension=768,              # 向量维度
    index_type="IVF_FLAT",      # 索引类型: IVF_FLAT, IVF_SQ8, HNSW
    metric_type="COSINE",       # 距离度量: COSINE, L2, IP
    nlist=1024                  # IVF参数
)
```

---

### 3. RAG 模块 (`core/rag/`)

#### 3.1 架构设计

```
core/rag/
├── __init__.py
├── embeddings.py    # 向量嵌入模型
├── retriever.py     # 文档检索器
└── chain.py         # RAG 链
```

#### 3.2 Embedding 模型

```python
from core.rag.embeddings import EmbeddingModel

# 初始化（默认使用 bge-base-zh-v1.5）
embedding = EmbeddingModel(
    model_name="BAAI/bge-base-zh-v1.5",  # 中文嵌入模型
    device="cpu"                          # 或 "cuda"
)

# 嵌入文本
vectors = embedding.embed(["文本1", "文本2"])

# 嵌入查询（会加query前缀优化）
query_vec = embedding.embed_query("查询问题")

# 获取维度
dim = embedding.dimension  # 768
```

#### 3.3 Retriever 检索器

```python
from core.rag.retriever import Retriever

retriever = Retriever(
    vector_store=vector_store,
    embedding_model=embedding_model,
    collection_name="my_docs",
    top_k=5,
    score_threshold=0.5  # 相似度阈值
)

# 添加文档
ids = await retriever.add_documents([
    {"content": "文档内容1", "metadata": {"source": "file1.txt"}},
    {"content": "文档内容2", "metadata": {"source": "file2.txt"}},
])

# 检索
results = await retriever.retrieve("查询问题", top_k=3)
for r in results:
    print(f"Score: {r.score}, Content: {r.content}")
```

#### 3.4 RAG Chain

```python
from core.rag.chain import RAGChain

rag = RAGChain(
    llm=llm,
    retriever=retriever,
    template="""基于以下上下文回答问题。

上下文:
{context}

问题: {question}

回答:""",
    include_sources=True,     # 返回来源
    max_context_length=4000   # 上下文最大长度
)

# 查询
result = await rag.query(
    question="什么是RAG？",
    top_k=5,
    filters={"source": "official_docs"}  # 可选过滤
)

print(result["answer"])
print(result["sources"])  # 来源文档

# 流式查询
async for chunk in rag.stream_query("什么是RAG？"):
    print(chunk, end="")
```

---

### 4. 提示词模块 (`core/prompt/`)

#### 4.1 架构设计

```
core/prompt/
├── __init__.py
├── manager.py       # 模板管理器
├── router.py        # 路由器
└── templates/       # 模板文件（可选）
```

#### 4.2 PromptManager 模板管理

```python
from core.prompt.manager import PromptManager, PromptTemplate

manager = PromptManager()

# 注册模板
manager.register(PromptTemplate(
    name="customer_service",
    template="""你是{company}的客服助手。

用户问题: {question}

请用专业、友好的语气回答。""",
    description="客服场景提示词",
    variables=["company", "question"],
    category="service"
))

# 获取并格式化
template = manager.get("customer_service")
prompt = template.format(company="XX公司", question="如何退款？")

# 列出所有模板
templates = manager.list_templates(category="service")

# 保存/加载
manager.save_to_file("prompts.json")
manager.load_from_file("prompts.json")
```

#### 4.3 PromptRouter 智能路由

```python
from core.prompt.router import PromptRouter, RouteRule, RouterStrategy

router = PromptRouter(prompt_manager=manager)

# 添加路由规则
router.add_rule(RouteRule(
    name="translate_route",
    template_name="translate",
    strategy=RouterStrategy.KEYWORD,
    keywords=["翻译", "translate", "转换成"],
    priority=10
))

router.add_rule(RouteRule(
    name="code_route",
    template_name="code_review",
    strategy=RouterStrategy.REGEX,
    pattern=r"(审查|review|检查).*代码",
    priority=10
))

# 自动路由
template = await router.route("帮我翻译这段话")
# 返回 translate 模板

# LLM智能路由
router.llm = llm
router.add_rule(RouteRule(
    name="smart_route",
    template_name="general",
    strategy=RouterStrategy.LLM,
    priority=1  # 最低优先级，兜底
))
```

---

### 5. 记忆模块 (`core/memory/`)

#### 5.1 架构设计

```
core/memory/
├── __init__.py
├── base.py          # 抽象基类
├── short_term.py    # 短期记忆（滑动窗口）
├── long_term.py     # 长期记忆（向量存储）
└── manager.py       # 统一管理器
```

#### 5.2 短期记忆 (ShortTermMemory)

```python
from core.memory.short_term import ShortTermMemory

memory = ShortTermMemory(
    max_size=10,           # 最多保留10条
    session_id="session1"
)

# 添加消息
await memory.add_user_message("你好")
await memory.add_assistant_message("你好！有什么可以帮你的？")

# 获取最近消息
recent = await memory.get_recent(5)

# 转换为LLM消息格式
messages = memory.to_messages()

# 获取上下文窗口（token限制）
context = await memory.get_context_window(max_tokens=4000)
```

#### 5.3 长期记忆 (LongTermMemory)

```python
from core.memory.long_term import LongTermMemory

memory = LongTermMemory(
    vector_store=vector_store,
    embedding_model=embedding_model,
    collection_name="user_memory",
    user_id="user123"
)

# 添加记忆
await memory.add(MemoryItem(
    content="用户喜欢Python编程",
    role="system",
    importance=0.8,
    metadata={"type": "preference"}
))

# 语义搜索
results = await memory.search("编程语言偏好", limit=5)

# 获取重要记忆
important = await memory.get_by_importance(min_importance=0.7)
```

#### 5.4 MemoryManager 统一管理

```python
from core.memory.manager import MemoryManager

manager = MemoryManager(
    short_term=short_term_memory,
    long_term=long_term_memory,
    llm=llm,                    # 用于摘要
    auto_archive=True,          # 自动归档重要记忆
    archive_threshold=0.6       # 归档阈值
)

# 添加对话
await manager.add_conversation_turn(
    user_message="我想学习AI",
    assistant_message="太好了！你对哪个方向感兴趣？"
)

# 获取对话历史
history = await manager.get_conversation_history(max_turns=5)

# 搜索所有记忆
results = await manager.search_all("AI学习", include_long_term=True)

# 摘要并归档
summary_id = await manager.summarize_and_archive(max_items=20)
```

---

### 6. 微调模块 (`core/finetune/`)

#### 6.1 架构设计

```
core/finetune/
├── __init__.py
├── data_processor.py    # 数据处理
├── trainer.py           # 训练器
└── lora_adapter.py      # LoRA适配器
```

#### 6.2 数据处理 (DataProcessor)

```python
from core.finetune.data_processor import DataProcessor, TrainingExample

processor = DataProcessor(format="alpaca")

# 创建训练样本
examples = [
    TrainingExample(
        instruction="翻译成英文",
        input="你好世界",
        output="Hello World"
    ),
    TrainingExample(
        instruction="总结以下文本",
        input="很长的文本...",
        output="简短摘要"
    )
]

# 验证数据
report = processor.validate_examples(examples)
print(f"有效: {report['valid']}, 无效: {report['invalid']}")

# 转换格式
alpaca_data = processor.convert(examples, target_format="alpaca")
openai_data = processor.convert(examples, target_format="openai")
sharegpt_data = processor.convert(examples, target_format="sharegpt")

# 保存数据
processor.save_jsonl(alpaca_data, "train.jsonl")

# 分割数据集
train, val = processor.split_dataset(examples, train_ratio=0.9)

# 转HuggingFace Dataset
hf_dataset = processor.to_hf_dataset(examples, tokenizer=tokenizer)
```

#### 6.3 LoRA 微调

```python
from core.finetune.lora_adapter import LoRAAdapter, LoRAConfig

# 配置
config = LoRAConfig(
    r=8,                    # LoRA rank
    lora_alpha=16,          # Alpha
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    use_4bit=True,          # 4bit量化
)

# 创建适配器
adapter = LoRAAdapter(
    base_model_path="meta-llama/Llama-2-7b-hf",
    config=config
)

# 加载模型并应用LoRA
adapter.load_base_model()
adapter.apply_lora()

# 保存适配器
adapter.save_adapter("./my_lora_adapter")

# 加载适配器
adapter.load_adapter("./my_lora_adapter")

# 合并权重
adapter.merge_and_save("./merged_model")

# 推理
response = adapter.generate("你好", max_new_tokens=100)
```

#### 6.4 全量微调 (FineTuneTrainer)

```python
from core.finetune.trainer import FineTuneTrainer, TrainingConfig

config = TrainingConfig(
    model_name_or_path="meta-llama/Llama-2-7b-hf",
    output_dir="./finetuned_model",
    num_train_epochs=3,
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    max_seq_length=2048,
    use_lora=False,          # 全量微调
    fp16=True,               # 混合精度
)

trainer = FineTuneTrainer(config)
trainer.load_model()

# 训练
result = trainer.train(train_dataset, eval_dataset)
print(f"Loss: {result['train_loss']}")

# 保存
trainer.save_model()

# 推理
response = trainer.generate("测试提示")
```

---

## API接口规范

### 认证流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │     │   API    │     │   Auth   │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │ POST /register │                │
     │───────────────>│                │
     │                │ create user    │
     │                │───────────────>│
     │                │<───────────────│
     │<───────────────│                │
     │                │                │
     │ POST /token    │                │
     │───────────────>│                │
     │                │ verify & sign  │
     │                │───────────────>│
     │                │<───────────────│
     │<───────────────│                │
     │   JWT Token    │                │
     │                │                │
     │ GET /protected │                │
     │ Authorization: │                │
     │ Bearer <token> │                │
     │───────────────>│                │
     │                │ verify token   │
     │                │───────────────>│
     │                │<───────────────│
     │<───────────────│                │
     │   Response     │                │
```

### API 端点详情

#### 认证 (`/api/v1/auth`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/register` | POST | 注册新用户 | 否 |
| `/token` | POST | 获取JWT令牌 | 否 |
| `/login` | POST | 表单登录 | 否 |
| `/me` | GET | 获取当前用户 | 是 |
| `/refresh` | POST | 刷新令牌 | 是 |

#### 对话 (`/api/v1/chat`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/completions` | POST | 对话补全 | 是 |
| `/completions/stream` | POST | 流式对话 | 是 |
| `/models` | GET | 列出模型 | 是 |
| `/route` | POST | 提示词路由 | 是 |

#### RAG (`/api/v1/rag`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/collections` | POST | 创建集合 | 是 |
| `/collections/{name}` | DELETE | 删除集合 | 是 |
| `/documents` | POST | 上传文档 | 是 |
| `/query` | POST | RAG查询 | 是 |
| `/query/stream` | POST | 流式RAG | 是 |
| `/search` | GET | 文档搜索 | 是 |

#### 记忆 (`/api/v1/memory`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/items` | POST | 添加记忆 | 是 |
| `/search` | POST | 搜索记忆 | 是 |
| `/history` | POST | 获取历史 | 是 |
| `/stats/{session_id}` | GET | 统计信息 | 是 |
| `/clear` | POST | 清除记忆 | 是 |
| `/archive/{session_id}` | POST | 归档记忆 | 是 |

#### 微调 (`/api/v1/finetune`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/datasets` | POST | 上传数据集 | 是 |
| `/datasets` | GET | 列出数据集 | 是 |
| `/train` | POST | 开始训练 | 是 |
| `/train/{job_id}` | GET | 训练状态 | 是 |
| `/models` | GET | 列出模型 | 是 |

#### WebSocket

| 端点 | 描述 |
|------|------|
| `/ws/chat?token=xxx&session_id=xxx` | 流式对话 |
| `/ws/rag?token=xxx&collection_name=xxx` | 流式RAG |

---

## 扩展开发指南

### 添加新的向量数据库

```python
# core/vector_store/pinecone_store.py
from core.vector_store.base import BaseVectorStore

class PineconeVectorStore(BaseVectorStore):
    def __init__(self, api_key: str, environment: str):
        import pinecone
        pinecone.init(api_key=api_key, environment=environment)
        self.index = None
    
    async def create_collection(self, collection_name: str, dimension: int, **kwargs):
        import pinecone
        if collection_name not in pinecone.list_indexes():
            pinecone.create_index(collection_name, dimension=dimension)
        self.index = pinecone.Index(collection_name)
        return True
    
    async def insert(self, collection_name: str, documents: List[Document]):
        vectors = [
            (doc.id, doc.embedding, {"content": doc.content, **doc.metadata})
            for doc in documents
        ]
        self.index.upsert(vectors)
        return [doc.id for doc in documents]
    
    async def search(self, collection_name: str, query_vector: List[float], 
                     top_k: int = 5, filters: dict = None):
        results = self.index.query(query_vector, top_k=top_k, include_metadata=True)
        return [
            SearchResult(id=r.id, content=r.metadata["content"], score=r.score)
            for r in results.matches
        ]
```

### 添加新的 API 路由

```python
# app/api/routes/my_feature.py
from fastapi import APIRouter, Depends
from app.api.auth import get_current_user

router = APIRouter(prefix="/my-feature", tags=["MyFeature"])

@router.post("/action")
async def my_action(
    data: MyRequest,
    current_user = Depends(get_current_user)
):
    # 实现逻辑
    return {"result": "success"}

# 在 app/api/routes/__init__.py 添加
from app.api.routes.my_feature import router as my_feature_router

# 在 app/main.py 注册
app.include_router(my_feature_router, prefix=api_prefix)
```

---

## 配置说明

### 环境变量完整列表

```bash
# === 应用配置 ===
APP_NAME=AI Agent Framework
APP_ENV=development          # development / production
DEBUG=true

# === JWT认证 ===
JWT_SECRET_KEY=your-secret-key-must-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# === OpenAI ===
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1

# === 通义千问 ===
DASHSCOPE_API_KEY=sk-xxx

# === LLaMA ===
LLAMA_MODEL_PATH=/path/to/model
LLAMA_API_BASE=http://localhost:8080

# === Milvus ===
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=
MILVUS_DB_NAME=ai_agent

# === Embedding ===
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
EMBEDDING_DEVICE=cpu          # cpu / cuda

# === 默认LLM ===
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL_NAME=gpt-3.5-turbo
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2048

# === 记忆 ===
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_COLLECTION=long_term_memory

# === 微调 ===
FINETUNE_OUTPUT_DIR=./finetune_output
FINETUNE_LOGGING_DIR=./finetune_logs
```

---

## 部署指南

### Docker 部署

```bash
# 构建镜像
docker build -t ai-agent-framework .

# 运行（需要先启动Milvus）
docker run -d \
  --name ai-agent \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/finetune_output:/app/finetune_output \
  ai-agent-framework

# 一键部署（包含Milvus）
docker-compose up -d
```

### 生产环境建议

1. **安全配置**
   - 修改 `JWT_SECRET_KEY` 为强随机字符串
   - 配置 CORS 白名单
   - 启用 HTTPS

2. **性能优化**
   - 使用 Gunicorn 多 worker
   - 配置连接池
   - 启用缓存

3. **监控**
   - 集成 Prometheus 指标
   - 配置日志收集
   - 设置告警

```bash
# 生产启动命令
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

---

## 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangChain 1.x 文档](https://python.langchain.com/docs/)
- [Milvus 文档](https://milvus.io/docs)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [PEFT 文档](https://huggingface.co/docs/peft)

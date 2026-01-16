# AI Agent Framework

一个功能完整的 AI Agent 开发框架，基于 **LangChain 1.x + FastAPI + Python**，支持多模型调用、RAG检索增强、提示词路由、记忆管理和模型微调。

## ✨ 特性

- 🤖 **多模型支持**: OpenAI (GPT-3.5/4), 通义千问 (Qwen), LLaMA
- 📚 **RAG系统**: 基于 Milvus 向量数据库的检索增强生成
- 🧠 **记忆管理**: 短期记忆 + 长期向量化记忆
- 🎯 **提示词路由**: 支持关键词、正则、LLM智能路由
- 🔧 **模型微调**: 支持全量微调和 LoRA 高效微调
- 🔐 **JWT认证**: 完整的用户认证系统
- 🌊 **WebSocket**: 流式输出支持

## 📁 项目结构

```
ai_agent_framework/
├── app/                        # FastAPI 应用
│   ├── main.py                # 应用入口
│   ├── config.py              # 配置管理
│   └── api/
│       ├── auth.py            # JWT认证
│       ├── deps.py            # 依赖注入
│       └── routes/            # API路由
│           ├── auth.py        # 认证接口
│           ├── chat.py        # 对话接口
│           ├── rag.py         # RAG接口
│           ├── memory.py      # 记忆接口
│           ├── finetune.py    # 微调接口
│           └── websocket.py   # WebSocket接口
├── core/                       # 核心模块
│   ├── llm/                   # LLM多模型支持
│   │   ├── base.py           # 基类
│   │   ├── openai_llm.py     # OpenAI
│   │   ├── qwen_llm.py       # 通义千问
│   │   ├── llama_llm.py      # LLaMA
│   │   └── factory.py        # 工厂模式
│   ├── vector_store/          # 向量数据库
│   │   ├── base.py           # 基类
│   │   └── milvus_store.py   # Milvus实现
│   ├── rag/                   # RAG模块
│   │   ├── embeddings.py     # 向量嵌入
│   │   ├── retriever.py      # 检索器
│   │   └── chain.py          # RAG链
│   ├── prompt/                # 提示词管理
│   │   ├── manager.py        # 模板管理
│   │   └── router.py         # 路由器
│   ├── memory/                # 记忆模块
│   │   ├── base.py           # 基类
│   │   ├── short_term.py     # 短期记忆
│   │   ├── long_term.py      # 长期记忆
│   │   └── manager.py        # 记忆管理器
│   └── finetune/              # 微调模块
│       ├── data_processor.py # 数据处理
│       ├── trainer.py        # 训练器
│       └── lora_adapter.py   # LoRA适配器
├── schemas/                    # Pydantic模型
├── utils/                      # 工具模块
├── .env.example               # 环境变量示例
├── requirements.txt           # 依赖
└── README.md
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd ai_agent_framework

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件，配置以下必要项：
# - OPENAI_API_KEY (如果使用OpenAI)
# - DASHSCOPE_API_KEY (如果使用通义千问)
# - JWT_SECRET_KEY (生产环境务必修改)
```

### 3. 启动 Milvus (Docker)

```bash
# 下载 docker-compose 文件
wget https://github.com/milvus-io/milvus/releases/download/v2.3.6/milvus-standalone-docker-compose.yml -O docker-compose.yml

# 启动 Milvus
docker-compose up -d
```

### 4. 启动服务

```bash
# 开发模式
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

## 📖 API 使用示例

### 认证

```python
import httpx

# 注册用户
response = httpx.post("http://localhost:8000/api/v1/auth/register", json={
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
})

# 登录获取token
response = httpx.post("http://localhost:8000/api/v1/auth/token", json={
    "username": "testuser",
    "password": "testpass123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

### 对话

```python
# 普通对话
response = httpx.post(
    "http://localhost:8000/api/v1/chat/completions",
    headers=headers,
    json={
        "messages": [
            {"role": "user", "content": "你好，介绍一下自己"}
        ],
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }
)
print(response.json()["content"])
```

### RAG 查询

```python
# 上传文档
response = httpx.post(
    "http://localhost:8000/api/v1/rag/documents",
    headers=headers,
    json={
        "documents": [
            {"content": "AI Agent是一种智能代理系统...", "metadata": {"source": "doc1"}},
            {"content": "RAG是检索增强生成技术...", "metadata": {"source": "doc2"}}
        ],
        "collection_name": "my_docs"
    }
)

# RAG查询
response = httpx.post(
    "http://localhost:8000/api/v1/rag/query",
    headers=headers,
    json={
        "question": "什么是RAG？",
        "collection_name": "my_docs",
        "top_k": 3
    }
)
print(response.json()["answer"])
```

### WebSocket 流式对话

```python
import asyncio
import websockets
import json

async def chat_stream():
    uri = f"ws://localhost:8000/ws/chat?token={token}&session_id=session1"
    
    async with websockets.connect(uri) as ws:
        # 发送消息
        await ws.send(json.dumps({
            "action": "chat",
            "messages": [{"role": "user", "content": "写一首关于AI的诗"}],
            "model": "gpt-3.5-turbo"
        }))
        
        # 接收流式响应
        while True:
            response = await ws.recv()
            data = json.loads(response)
            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
            elif data["type"] == "end":
                break

asyncio.run(chat_stream())
```

### 模型微调

```python
# 上传数据集
response = httpx.post(
    "http://localhost:8000/api/v1/finetune/datasets",
    headers=headers,
    json={
        "name": "my_dataset",
        "format": "alpaca",
        "examples": [
            {"instruction": "翻译成英文", "input": "你好", "output": "Hello"},
            {"instruction": "翻译成英文", "input": "谢谢", "output": "Thank you"}
        ]
    }
)

# 开始训练
response = httpx.post(
    "http://localhost:8000/api/v1/finetune/train",
    headers=headers,
    json={
        "dataset_name": "my_dataset",
        "config": {
            "model_name_or_path": "meta-llama/Llama-2-7b-hf",
            "output_name": "my_finetuned_model",
            "use_lora": True,
            "num_train_epochs": 3
        }
    }
)
job_id = response.json()["job_id"]

# 查询训练状态
response = httpx.get(
    f"http://localhost:8000/api/v1/finetune/train/{job_id}",
    headers=headers
)
print(response.json()["status"])
```

## 🔧 扩展开发

### 添加新的LLM提供商

```python
from core.llm.base import BaseLLM, Message, LLMResponse
from core.llm.factory import LLMFactory

class MyCustomLLM(BaseLLM):
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        # 实现生成逻辑
        pass
    
    async def stream_generate(self, messages: List[Message], **kwargs):
        # 实现流式生成
        pass
    
    def get_provider_name(self) -> str:
        return "my_provider"

# 注册到工厂
LLMFactory.register_provider("my_provider", MyCustomLLM)
```

### 添加自定义提示词模板

```python
from core.prompt.manager import PromptManager, PromptTemplate

manager = PromptManager()
manager.register(PromptTemplate(
    name="my_template",
    template="根据以下信息回答: {context}\n问题: {question}",
    variables=["context", "question"],
    category="custom"
))
```

### 添加自定义路由规则

```python
from core.prompt.router import PromptRouter, RouteRule, RouterStrategy

router = PromptRouter(prompt_manager)
router.add_rule(RouteRule(
    name="custom_route",
    template_name="my_template",
    strategy=RouterStrategy.KEYWORD,
    keywords=["特殊关键词", "custom"],
    priority=20
))
```

## 📋 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/token` | POST | 获取JWT令牌 |
| `/api/v1/chat/completions` | POST | 对话补全 |
| `/api/v1/chat/completions/stream` | POST | 流式对话 |
| `/api/v1/rag/documents` | POST | 上传文档 |
| `/api/v1/rag/query` | POST | RAG查询 |
| `/api/v1/memory/items` | POST | 添加记忆 |
| `/api/v1/memory/search` | POST | 搜索记忆 |
| `/api/v1/finetune/datasets` | POST | 上传数据集 |
| `/api/v1/finetune/train` | POST | 开始训练 |
| `/ws/chat` | WebSocket | 流式对话 |
| `/ws/rag` | WebSocket | 流式RAG |

## ⚙️ 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `DASHSCOPE_API_KEY` | 通义千问API密钥 | - |
| `MILVUS_HOST` | Milvus地址 | localhost |
| `MILVUS_PORT` | Milvus端口 | 19530 |
| `JWT_SECRET_KEY` | JWT密钥 | - |
| `EMBEDDING_MODEL` | 嵌入模型 | BAAI/bge-base-zh-v1.5 |
| `DEFAULT_LLM_PROVIDER` | 默认LLM提供商 | openai |

## 🛠️ 技术栈

- **Web框架**: FastAPI
- **LLM框架**: LangChain 1.x (LCEL)
- **向量数据库**: Milvus
- **嵌入模型**: SentenceTransformers
- **微调**: HuggingFace Transformers + PEFT
- **认证**: JWT (python-jose)

## 📄 License

MIT License

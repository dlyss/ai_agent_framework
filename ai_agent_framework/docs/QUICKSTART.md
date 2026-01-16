# 🚀 AI Agent Framework 快速入门指南

本指南帮助你在 **10分钟内** 快速启动和使用 AI Agent Framework。

---

## 📋 目录

- [环境要求](#环境要求)
- [快速安装](#快速安装)
- [启动服务](#启动服务)
- [第一个请求](#第一个请求)
- [常用场景示例](#常用场景示例)
- [下一步](#下一步)

---

## 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | >= 3.9 |
| Docker | >= 20.0 (用于Milvus) |
| 内存 | >= 8GB 推荐 |

---

## 快速安装

### 方式一：本地安装 (推荐开发)

```bash
# 1. 进入项目目录
cd ai_agent_framework

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
```

编辑 `.env` 文件，配置必要的 API Key：

```bash
# 至少配置一个 LLM 提供商
OPENAI_API_KEY=sk-your-openai-key

# 或使用通义千问
DASHSCOPE_API_KEY=sk-your-dashscope-key

# JWT密钥（生产环境必须修改）
JWT_SECRET_KEY=your-secret-key-change-this
```

### 方式二：Docker 一键部署

```bash
# 复制环境配置
cp .env.example .env
# 编辑 .env 配置 API Keys

# 一键启动所有服务
docker-compose up -d
```

---

## 启动服务

### 1. 启动 Milvus 向量数据库

```bash
# 使用 docker-compose 启动 Milvus
docker-compose up -d etcd minio milvus

# 验证 Milvus 是否启动成功
curl http://localhost:9091/healthz
# 返回 OK 表示成功
```

### 2. 启动 API 服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python -m app.main
```

### 3. 验证服务

打开浏览器访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 第一个请求

### Step 1: 注册用户

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo123456",
    "email": "demo@example.com"
  }'
```

响应：
```json
{
  "id": "xxx-xxx-xxx",
  "username": "demo",
  "email": "demo@example.com",
  "is_active": true
}
```

### Step 2: 获取 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "demo123456"
  }'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**保存这个 token**，后续请求都需要用到。

### Step 3: 发起对话

```bash
export TOKEN="你的access_token"

curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "model": "gpt-3.5-turbo"
  }'
```

响应：
```json
{
  "content": "你好！我是一个AI助手...",
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60}
}
```

🎉 **恭喜！你已成功完成第一个请求！**

---

## 常用场景示例

### 场景1：带记忆的多轮对话

```bash
# 第一轮对话（指定 session_id）
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "我叫小明"}],
    "session_id": "session-001"
  }'

# 第二轮对话（同一 session_id，AI会记住你的名字）
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "我叫什么名字？"}],
    "session_id": "session-001"
  }'
```

### 场景2：RAG 知识库问答

```bash
# Step 1: 上传文档
curl -X POST "http://localhost:8000/api/v1/rag/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"content": "公司成立于2020年，主营业务是AI解决方案", "metadata": {"source": "company_intro"}},
      {"content": "产品包括智能客服、知识库、AI助手等", "metadata": {"source": "products"}}
    ],
    "collection_name": "company_docs"
  }'

# Step 2: 基于文档问答
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "公司有哪些产品？",
    "collection_name": "company_docs",
    "top_k": 3
  }'
```

### 场景3：WebSocket 流式对话

```python
import asyncio
import websockets
import json

async def stream_chat():
    token = "你的access_token"
    uri = f"ws://localhost:8000/ws/chat?token={token}"
    
    async with websockets.connect(uri) as ws:
        # 发送请求
        await ws.send(json.dumps({
            "action": "chat",
            "messages": [{"role": "user", "content": "写一首关于春天的诗"}]
        }))
        
        # 接收流式响应
        while True:
            response = await ws.recv()
            data = json.loads(response)
            
            if data["type"] == "chunk":
                print(data["content"], end="", flush=True)
            elif data["type"] == "end":
                print("\n--- 完成 ---")
                break

asyncio.run(stream_chat())
```

### 场景4：使用不同的模型

```bash
# 使用 GPT-4
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "解释量子计算"}],
    "provider": "openai",
    "model": "gpt-4"
  }'

# 使用通义千问
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "解释量子计算"}],
    "provider": "qwen",
    "model": "qwen-turbo"
  }'
```

---

## Python SDK 快速使用

```python
import httpx

class AIAgentClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def login(self, username: str, password: str):
        resp = httpx.post(f"{self.base_url}/api/v1/auth/token", json={
            "username": username,
            "password": password
        })
        self.token = resp.json()["access_token"]
    
    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def chat(self, message: str, session_id: str = None):
        resp = httpx.post(
            f"{self.base_url}/api/v1/chat/completions",
            headers=self.headers,
            json={
                "messages": [{"role": "user", "content": message}],
                "session_id": session_id
            }
        )
        return resp.json()["content"]
    
    def rag_query(self, question: str, collection: str = "default"):
        resp = httpx.post(
            f"{self.base_url}/api/v1/rag/query",
            headers=self.headers,
            json={"question": question, "collection_name": collection}
        )
        return resp.json()

# 使用示例
client = AIAgentClient()
client.login("demo", "demo123456")

# 普通对话
print(client.chat("你好"))

# 带记忆的对话
print(client.chat("我叫小明", session_id="s1"))
print(client.chat("我叫什么？", session_id="s1"))
```

---

## 常见问题

### Q: Milvus 连接失败？

```bash
# 检查 Milvus 状态
docker ps | grep milvus
docker logs milvus-standalone

# 确保端口 19530 未被占用
lsof -i :19530
```

### Q: OpenAI API 调用失败？

```bash
# 检查 API Key 是否正确
echo $OPENAI_API_KEY

# 检查网络连接（可能需要代理）
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Q: Token 过期？

```bash
# 刷新 Token
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Authorization: Bearer $OLD_TOKEN"
```

---

## 下一步

- 📖 阅读 [详细开发文档](./DEVELOPMENT.md)
- 🔧 了解 [API 完整参考](./API_REFERENCE.md)
- 🎯 查看 [最佳实践](./BEST_PRACTICES.md)
- 💡 探索 [示例项目](../examples/)

---

## 获取帮助

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **GitHub Issues**: 提交问题反馈

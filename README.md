# AI Agent 全栈项目

基于 **Python + FastAPI + Next.js** 的 AI Agent 全栈解决方案，支持多模型调用、RAG知识库、记忆管理和模型微调。

---

## 🏗️ 项目结构

```
AiCareer/
├── ai_agent_framework/     # 后端 - Python FastAPI
│   ├── app/               # FastAPI应用
│   ├── core/              # 核心模块（LLM/RAG/Memory/Finetune）
│   ├── schemas/           # Pydantic模型
│   └── docs/              # 后端文档
├── ai_agent_web/          # 前端 - Next.js React
│   ├── app/               # 页面
│   ├── components/        # 组件
│   ├── lib/               # 工具和状态
│   └── docs/              # 前端文档
├── start.sh               # 一键启动脚本
└── README.md              # 本文档
```

---

## ✨ 功能特性

### 后端功能

| 模块 | 功能 |
|------|------|
| **多模型LLM** | OpenAI/GPT、通义千问、LLaMA |
| **RAG检索** | Milvus向量库 + BGE嵌入模型 |
| **记忆系统** | 短期滑动窗口 + 长期向量存储 |
| **提示词路由** | 关键词/正则/LLM智能路由 |
| **模型微调** | 全量微调 + LoRA/QLoRA |
| **认证系统** | JWT Token + MySQL存储 |
| **流式输出** | WebSocket实时推送 |

### 前端功能

| 页面 | 功能 |
|------|------|
| `/login` | 用户登录 |
| `/register` | 用户注册 |
| `/chat` | AI对话（流式输出） |
| `/rag` | 知识库管理和问答 |

---

## 🚀 快速开始

### 默认账号

| 用户名 | 密码 | 权限 |
|--------|--------|------|
| admin | 111111 | 超级管理员 |

### 方式一：一键启动

```bash
# 赋予执行权限
chmod +x start.sh

# 启动所有服务
./start.sh
```

### 方式二：手动启动

#### 1. 启动数据库

```bash
cd ai_agent_framework
docker-compose up -d mysql milvus etcd minio
```

#### 2. 启动后端

```bash
cd ai_agent_framework

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 配置API Keys

# 启动服务
uvicorn app.main:app --reload --port 8000
```

#### 3. 启动前端

```bash
cd ai_agent_web

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动服务
npm run dev
```

---

## 🔐 默认账号

| 用户名 | 密码 | 权限 |
|--------|------|------|
| admin | 111111 | 超级管理员 |

---

## 📋 API文档

启动后端后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/token` | POST | 登录获取Token |
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/chat/completions` | POST | 对话补全 |
| `/api/v1/rag/documents` | POST | 上传文档 |
| `/api/v1/rag/query` | POST | RAG问答 |
| `/ws/chat` | WebSocket | 流式对话 |

---

## ⚙️ 环境变量

### 后端 (.env)

```bash
# LLM API Keys
OPENAI_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=ai_agent

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# JWT
JWT_SECRET_KEY=your-secret-key
```

### 前端 (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_HOST=localhost:8000
```

---

## 🛠️ 技术栈

### 后端

- **Web框架**: FastAPI
- **LLM**: LangChain 1.x (LCEL) + OpenAI/DashScope
- **向量数据库**: Milvus
- **关系数据库**: MySQL + SQLAlchemy
- **认证**: JWT (python-jose)
- **微调**: HuggingFace Transformers + PEFT

### 前端

- **框架**: Next.js 15 (App Router)
- **UI**: React 19 + TypeScript
- **样式**: TailwindCSS + shadcn/ui
- **状态**: Zustand
- **请求**: Axios + WebSocket

---

## 📚 文档

| 文档 | 位置 |
|------|------|
| 后端快速入门 | `ai_agent_framework/docs/QUICKSTART.md` |
| 后端开发文档 | `ai_agent_framework/docs/DEVELOPMENT.md` |
| 前端快速入门 | `ai_agent_web/docs/QUICKSTART.md` |
| 前端开发文档 | `ai_agent_web/docs/DEVELOPMENT.md` |

---

## 🐳 Docker部署

```bash
cd ai_agent_framework
docker-compose up -d
```

包含服务：
- MySQL 8.0
- Milvus 2.3
- AI Agent Backend

---

## 📄 License

MIT License

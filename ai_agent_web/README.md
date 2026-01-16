# AI Agent Web

基于 Next.js 15 + React 19 + TypeScript 的 AI Agent 前端应用。

## 技术栈

- **框架**: Next.js 15 (App Router)
- **UI**: React 19 + TypeScript
- **样式**: TailwindCSS + shadcn/ui
- **状态管理**: Zustand
- **API请求**: Axios + React Query

## 功能

- 用户认证（登录/注册）
- AI 对话（WebSocket 流式）
- RAG 知识库问答
- 响应式设计

## 快速开始

### 默认账号

| 用户名 | 密码 | 权限 |
|--------|--------|------|
| admin | 111111 | 超级管理员 |

### 启动

```bash
# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## 项目结构

```
ai_agent_web/
├── app/                 # Next.js App Router
│   ├── login/          # 登录页
│   ├── register/       # 注册页
│   ├── chat/           # 对话页
│   └── rag/            # RAG页
├── components/
│   └── ui/             # UI组件
├── lib/
│   ├── api/            # API封装
│   └── store/          # Zustand状态
└── types/              # TypeScript类型
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| NEXT_PUBLIC_API_URL | 后端API地址 | http://localhost:8000/api/v1 |
| NEXT_PUBLIC_WS_HOST | WebSocket地址 | localhost:8000 |

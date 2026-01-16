# 🚀 AI Agent Web 快速上手指南

5分钟快速启动前端项目。

---

## 环境要求

- Node.js >= 18
- npm >= 9

---

## 快速启动

### 1. 安装依赖

```bash
cd ai_agent_web
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
```

编辑 `.env.local`：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_HOST=localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

---

## 默认账号

| 用户名 | 密码 | 权限 |
|--------|------|------|
| admin | 111111 | 超级管理员 |

---

## 页面说明

### 登录页 `/login`

输入用户名和密码登录系统。

### 注册页 `/register`

新用户注册，需填写：
- 用户名（3-50字符）
- 邮箱
- 密码（6位以上）

### 对话页 `/chat`

- 左侧：侧边栏，显示用户信息
- 右侧：对话区域
- 支持 WebSocket 流式输出
- 点击"新对话"清空历史

### RAG页 `/rag`

- **上传文档**：输入文档内容，用空行分隔
- **RAG问答**：输入问题，返回基于知识库的回答

---

## 常见问题

### Q: 页面显示"未登录"？

检查：
1. 是否已登录
2. Token是否过期
3. 后端服务是否运行

### Q: WebSocket连接失败？

检查：
1. `NEXT_PUBLIC_WS_HOST` 配置是否正确
2. 后端WebSocket服务是否启动
3. 浏览器控制台错误信息

### Q: API请求失败？

检查：
1. `NEXT_PUBLIC_API_URL` 配置是否正确
2. 后端服务是否在 8000 端口运行
3. CORS配置是否正确

---

## 下一步

- 📖 阅读 [开发文档](./DEVELOPMENT.md)
- 🔧 了解 [API接口](../../ai_agent_framework/docs/DEVELOPMENT.md)

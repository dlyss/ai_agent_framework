# 📚 AI Agent Web 开发文档

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 15 | React框架 (App Router) |
| React | 19 | UI库 |
| TypeScript | 5.x | 类型安全 |
| TailwindCSS | 3.x | 样式 |
| shadcn/ui | - | UI组件库 |
| Zustand | 5.x | 状态管理 |
| Axios | 1.x | HTTP请求 |
| React Query | 5.x | 异步状态管理 |

---

## 项目结构

```
ai_agent_web/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # 根布局
│   ├── page.tsx             # 首页（重定向）
│   ├── globals.css          # 全局样式（Tailwind）
│   ├── login/page.tsx       # 登录页
│   ├── register/page.tsx    # 注册页
│   ├── chat/page.tsx        # 对话页
│   └── rag/page.tsx         # RAG页
├── components/
│   ├── providers.tsx        # React Query Provider
│   └── ui/                  # shadcn/ui 组件
├── lib/
│   ├── utils.ts             # 工具函数
│   ├── api/                 # API封装
│   │   ├── client.ts       # Axios实例
│   │   ├── auth.ts         # 认证API
│   │   ├── chat.ts         # 对话API
│   │   └── rag.ts          # RAG API
│   └── store/               # Zustand状态
│       ├── auth.ts         # 认证状态
│       └── chat.ts         # 对话状态
├── types/
│   └── index.ts             # TypeScript类型定义
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.ts
```

---

## API层设计

### client.ts - Axios配置

```typescript
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// 请求拦截器：自动添加Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

### API模块示例

```typescript
// lib/api/auth.ts
export const authApi = {
  async login(data: LoginRequest): Promise<Token> {
    const response = await apiClient.post<Token>("/auth/token", data);
    return response.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>("/auth/register", data);
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },
};
```

---

## 状态管理

### Zustand Store

```typescript
// lib/store/auth.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      login: async (username, password) => {
        const data = await authApi.login({ username, password });
        localStorage.setItem("access_token", data.access_token);
        set({ token: data.access_token });
        // 获取用户信息
        const user = await authApi.getMe();
        set({ user });
      },

      logout: () => {
        localStorage.removeItem("access_token");
        set({ token: null, user: null });
      },
    }),
    { name: "auth-storage" }
  )
);
```

### 使用示例

```tsx
"use client";

import { useAuthStore } from "@/lib/store/auth";

export default function SomeComponent() {
  const { user, logout } = useAuthStore();

  return (
    <div>
      <p>Welcome, {user?.username}</p>
      <button onClick={logout}>退出</button>
    </div>
  );
}
```

---

## WebSocket 流式输出

### 连接WebSocket

```typescript
// lib/api/client.ts
export function getWebSocketUrl(path: string): string {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = process.env.NEXT_PUBLIC_WS_HOST || "localhost:8000";
  return `${wsProtocol}//${host}${path}`;
}
```

### 对话页实现

```tsx
const wsRef = useRef<WebSocket | null>(null);

const connectWebSocket = () => {
  const ws = new WebSocket(
    getWebSocketUrl(`/ws/chat?token=${token}&session_id=${sessionId}`)
  );

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "chunk") {
      // 流式更新消息内容
      updateLastMessage(prev => prev + data.content);
    } else if (data.type === "end") {
      setLoading(false);
    }
  };

  wsRef.current = ws;
};

const sendMessage = () => {
  wsRef.current?.send(JSON.stringify({
    action: "chat",
    messages: [...messages, userMessage],
    model: "gpt-3.5-turbo",
  }));
};
```

---

## 组件开发

### shadcn/ui 组件

项目使用 shadcn/ui 作为组件库，组件位于 `components/ui/`。

**已集成组件：**
- Button
- Input
- Label
- Card
- Avatar
- ScrollArea
- Toast

### 添加新组件

参考 shadcn/ui 官网，手动创建组件文件：

```tsx
// components/ui/badge.tsx
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        variant === "default" && "bg-primary text-primary-foreground",
        variant === "secondary" && "bg-secondary text-secondary-foreground",
        variant === "destructive" && "bg-destructive text-destructive-foreground",
        className
      )}
      {...props}
    />
  );
}
```

---

## 添加新页面

### 1. 创建页面文件

```tsx
// app/settings/page.tsx
"use client";

import { useAuthStore } from "@/lib/store/auth";

export default function SettingsPage() {
  const { user } = useAuthStore();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">设置</h1>
      <p>用户: {user?.username}</p>
    </div>
  );
}
```

### 2. 添加路由保护

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth";

export default function ProtectedPage() {
  const router = useRouter();
  const { token } = useAuthStore();

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  if (!token) return null;

  return <div>受保护的内容</div>;
}
```

---

## 样式开发

### Tailwind CSS

使用 Tailwind 实用类：

```tsx
<div className="flex items-center justify-between p-4 bg-card rounded-lg shadow">
  <span className="text-lg font-medium">标题</span>
  <button className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90">
    按钮
  </button>
</div>
```

### CSS变量 (主题)

在 `app/globals.css` 中定义：

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  /* ... */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... */
}
```

---

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| NEXT_PUBLIC_API_URL | 后端API地址 | http://localhost:8000/api/v1 |
| NEXT_PUBLIC_WS_HOST | WebSocket地址 | localhost:8000 |

---

## 构建部署

### 开发

```bash
npm run dev
```

### 构建

```bash
npm run build
```

### 生产运行

```bash
npm run start
```

### Docker部署

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

---

## 调试技巧

### 1. 查看网络请求

浏览器 DevTools > Network

### 2. 查看WebSocket消息

浏览器 DevTools > Network > WS

### 3. 查看状态

```tsx
// 在组件中
const state = useAuthStore.getState();
console.log(state);
```

### 4. React DevTools

安装 React DevTools 浏览器扩展，查看组件树和状态。

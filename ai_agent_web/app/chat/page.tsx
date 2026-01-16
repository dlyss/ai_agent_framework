"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth";
import { useChatStore } from "@/lib/store/chat";
import { getWebSocketUrl } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  Send, 
  Loader2, 
  Bot, 
  User, 
  LogOut,
  Settings,
  Trash2,
  MessageSquare,
  FileText
} from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import type { Message } from "@/types";

export default function ChatPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();
  const { 
    messages, 
    isLoading, 
    sessionId,
    model,
    addMessage, 
    updateLastMessage, 
    clearMessages,
    setLoading 
  } = useChatStore();
  
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    const ws = new WebSocket(
      getWebSocketUrl(`/ws/chat?token=${token}&session_id=${sessionId}`)
    );
    
    ws.onopen = () => console.log("WebSocket connected");
    ws.onerror = (error) => console.error("WebSocket error:", error);
    ws.onclose = () => console.log("WebSocket closed");
    
    wsRef.current = ws;
    return ws;
  }, [token, sessionId]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    addMessage(userMessage);
    setInput("");
    setLoading(true);

    const assistantMessage: Message = { role: "assistant", content: "" };
    addMessage(assistantMessage);

    try {
      const ws = connectWebSocket();
      if (!ws) return;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "chunk") {
          updateLastMessage((messages[messages.length - 1]?.content || "") + data.content);
        } else if (data.type === "end") {
          setLoading(false);
        } else if (data.type === "error") {
          updateLastMessage("发生错误: " + data.message);
          setLoading(false);
        }
      };

      ws.send(JSON.stringify({
        action: "chat",
        messages: [...messages, userMessage].map(m => ({
          role: m.role,
          content: m.content
        })),
        model: model,
      }));
    } catch (error) {
      console.error("Send error:", error);
      updateLastMessage("发送消息失败，请重试");
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  if (!token) return null;

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-6 w-6 text-primary" />
              <span className="font-semibold">AI Agent</span>
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-9 w-9"
              onClick={() => router.push("/admin")}
              title="后台管理"
            >
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>
        
        <div className="flex-1 p-4 space-y-2">
          {/* 功能模块导航 */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground px-2 mb-2">功能模块</p>
            <Button 
              variant="default" 
              className="w-full justify-start gap-2 bg-primary text-primary-foreground"
            >
              <MessageSquare className="h-4 w-4" />
              AI 对话
            </Button>
            <Button 
              variant="ghost" 
              className="w-full justify-start gap-2 hover:bg-muted"
              onClick={() => router.push("/rag")}
            >
              <FileText className="h-4 w-4" />
              RAG 知识库
            </Button>
          </div>
          
          {/* 模型选择 */}
          <div className="border-t pt-4 mt-4">
            <p className="text-xs text-muted-foreground px-2 mb-2">模型设置</p>
            <select 
              className="w-full p-2 rounded-md border bg-background text-sm"
              value={model}
              onChange={(e) => useChatStore.getState().setModel(e.target.value)}
            >
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="qwen-turbo">通义千问 Turbo</option>
              <option value="qwen-plus">通义千问 Plus</option>
            </select>
          </div>
          
          <div className="border-t pt-4 mt-4">
            <p className="text-xs text-muted-foreground px-2 mb-2">对话操作</p>
            <Button 
              variant="outline" 
              className="w-full justify-start gap-2"
              onClick={clearMessages}
            >
              <MessageSquare className="h-4 w-4" />
              新建对话
            </Button>
          </div>
        </div>

        <div className="p-4 border-t space-y-3">
          <div className="flex items-center gap-2 px-2 py-1">
            <Avatar className="h-8 w-8">
              <AvatarFallback>{user?.username?.[0]?.toUpperCase() || "U"}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <span className="text-sm font-medium truncate block">{user?.username}</span>
              <span className="text-xs text-muted-foreground">已登录</span>
            </div>
          </div>
          <Button variant="outline" size="sm" className="w-full justify-start gap-2" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            退出登录
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-14 border-b flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <span className="font-medium">对话</span>
            <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
              {model}
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={clearMessages}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Bot className="h-12 w-12 mb-4" />
              <p className="text-lg font-medium">开始新对话</p>
              <p className="text-sm">输入消息与 AI 助手交流</p>
            </div>
          ) : (
            <div className="space-y-4 max-w-3xl mx-auto">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex gap-3",
                    message.role === "user" && "flex-row-reverse"
                  )}
                >
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback>
                      {message.role === "user" ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={cn(
                      "rounded-lg px-4 py-2 max-w-[80%]",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    )}
                  >
                    {message.role === "assistant" ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown>{message.content || "..."}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              )}
            </div>
          )}
        </ScrollArea>

        {/* Input */}
        <div className="border-t p-4">
          <div className="max-w-3xl mx-auto flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button onClick={sendMessage} disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth";
import { ragApi } from "@/lib/api/rag";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "@/components/ui/toaster";
import { ArrowLeft, Upload, Search, Loader2, FileText, Bot, MessageSquare, LogOut, Settings } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export default function RAGPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [collectionName, setCollectionName] = useState("default");
  const [documents, setDocuments] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<{ content: string; score: number }[]>([]);

  useEffect(() => {
    if (!token) router.replace("/login");
  }, [token, router]);

  const handleUpload = async () => {
    if (!documents.trim()) {
      toast({ title: "错误", description: "请输入文档内容", variant: "destructive" });
      return;
    }
    setIsLoading(true);
    try {
      const docs = documents.split("\n\n").filter(d => d.trim()).map(content => ({
        content: content.trim(),
        metadata: { source: "manual" }
      }));
      await ragApi.uploadDocuments({ documents: docs, collection_name: collectionName });
      toast({ title: "上传成功", description: `已上传 ${docs.length} 个文档` });
      setDocuments("");
    } catch {
      toast({ title: "上传失败", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!question.trim()) return;
    setIsLoading(true);
    setAnswer("");
    setSources([]);
    try {
      const result = await ragApi.query({
        question: question.trim(),
        collection_name: collectionName,
        top_k: 3,
        include_sources: true
      });
      setAnswer(result.answer);
      setSources(result.sources || []);
    } catch {
      toast({ title: "查询失败", variant: "destructive" });
    } finally {
      setIsLoading(false);
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
              variant="ghost" 
              className="w-full justify-start gap-2 hover:bg-muted"
              onClick={() => router.push("/chat")}
            >
              <MessageSquare className="h-4 w-4" />
              AI 对话
            </Button>
            <Button 
              variant="default" 
              className="w-full justify-start gap-2 bg-primary text-primary-foreground"
            >
              <FileText className="h-4 w-4" />
              RAG 知识库
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

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b flex items-center px-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <span className="font-medium">RAG 知识库</span>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6">
          <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" /> 上传文档
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>集合名称</Label>
                <Input value={collectionName} onChange={(e) => setCollectionName(e.target.value)} />
              </div>
              <div>
                <Label>文档内容（空行分隔）</Label>
                <textarea
                  className="w-full h-40 p-3 border rounded-md bg-background resize-none"
                  value={documents}
                  onChange={(e) => setDocuments(e.target.value)}
                  placeholder="文档1内容...\n\n文档2内容..."
                />
              </div>
              <Button onClick={handleUpload} disabled={isLoading} className="w-full">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Upload className="h-4 w-4 mr-2" />}
                上传
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" /> RAG 问答
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>问题</Label>
                <Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入问题..." />
              </div>
              <Button onClick={handleQuery} disabled={isLoading} className="w-full">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
                查询
              </Button>
              {answer && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="font-medium mb-2">回答：</p>
                  <p className="whitespace-pre-wrap">{answer}</p>
                </div>
              )}
              {sources.length > 0 && (
                <ScrollArea className="h-40">
                  <p className="font-medium mb-2">参考来源：</p>
                  {sources.map((s, i) => (
                    <div key={i} className="p-2 mb-2 bg-muted/50 rounded text-sm">
                      <FileText className="h-4 w-4 inline mr-1" />
                      <span className="text-muted-foreground">相似度: {(s.score * 100).toFixed(1)}%</span>
                      <p className="mt-1 line-clamp-2">{s.content}</p>
                    </div>
                  ))}
                </ScrollArea>
              )}
            </CardContent>
          </Card>
          </div>
        </main>
      </div>
    </div>
  );
}

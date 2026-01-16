"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/toaster";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  Bot, 
  MessageSquare, 
  FileText, 
  LogOut, 
  Settings,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  Loader2,
  Eye,
  EyeOff
} from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  api_key_masked: string;
  base_url: string;
  enabled: boolean;
}

interface ModelForm {
  id: string;
  name: string;
  provider: string;
  api_key: string;
  base_url: string;
  enabled: boolean;
}

const emptyForm: ModelForm = {
  id: "",
  name: "",
  provider: "openai",
  api_key: "",
  base_url: "",
  enabled: true,
};

export default function AdminPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [form, setForm] = useState<ModelForm>(emptyForm);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    if (!token) router.replace("/login");
    else fetchModels();
  }, [token, router]);

  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.get("/models");
      setModels(res.data);
    } catch {
      toast({ title: "获取模型列表失败", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdd = () => {
    setIsAdding(true);
    setEditingId(null);
    setForm(emptyForm);
    setShowApiKey(false);
  };

  const handleEdit = (model: ModelConfig) => {
    setEditingId(model.id);
    setIsAdding(false);
    setForm({
      id: model.id,
      name: model.name,
      provider: model.provider,
      api_key: "",
      base_url: model.base_url,
      enabled: model.enabled,
    });
    setShowApiKey(false);
  };

  const handleCancel = () => {
    setEditingId(null);
    setIsAdding(false);
    setForm(emptyForm);
  };

  const handleSave = async () => {
    if (!form.id || !form.name) {
      toast({ title: "请填写模型ID和名称", variant: "destructive" });
      return;
    }

    setIsLoading(true);
    try {
      if (isAdding) {
        await apiClient.post("/models", form);
        toast({ title: "模型添加成功" });
      } else {
        const updateData: Record<string, unknown> = {
          name: form.name,
          provider: form.provider,
          base_url: form.base_url,
          enabled: form.enabled,
        };
        if (form.api_key) {
          updateData.api_key = form.api_key;
        }
        await apiClient.put(`/models/${editingId}`, updateData);
        toast({ title: "模型更新成功" });
      }
      handleCancel();
      fetchModels();
    } catch {
      toast({ title: isAdding ? "添加失败" : "更新失败", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除该模型配置吗？")) return;
    
    setIsLoading(true);
    try {
      await apiClient.delete(`/models/${id}`);
      toast({ title: "模型已删除" });
      fetchModels();
    } catch {
      toast({ title: "删除失败", variant: "destructive" });
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
              variant="secondary" 
              size="icon" 
              className="h-9 w-9"
              title="后台管理（当前页面）"
            >
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>
        
        <div className="flex-1 p-4 space-y-2">
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
              variant="ghost" 
              className="w-full justify-start gap-2 hover:bg-muted"
              onClick={() => router.push("/rag")}
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
        <header className="h-14 border-b flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" />
            <span className="font-medium">后台管理 - 模型配置</span>
          </div>
          <Button onClick={handleAdd} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            添加模型
          </Button>
        </header>

        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            {/* 添加/编辑表单 */}
            {(isAdding || editingId) && (
              <Card className="border-primary">
                <CardHeader>
                  <CardTitle className="text-lg">
                    {isAdding ? "添加新模型" : "编辑模型"}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>模型ID *</Label>
                      <Input 
                        value={form.id} 
                        onChange={(e) => setForm({...form, id: e.target.value})}
                        placeholder="如: gpt-4-turbo"
                        disabled={!!editingId}
                      />
                    </div>
                    <div>
                      <Label>模型名称 *</Label>
                      <Input 
                        value={form.name} 
                        onChange={(e) => setForm({...form, name: e.target.value})}
                        placeholder="如: GPT-4 Turbo"
                      />
                    </div>
                    <div>
                      <Label>提供商</Label>
                      <select 
                        className="w-full p-2 rounded-md border bg-background"
                        value={form.provider}
                        onChange={(e) => setForm({...form, provider: e.target.value})}
                      >
                        <option value="openai">OpenAI</option>
                        <option value="dashscope">阿里云 DashScope</option>
                        <option value="azure">Azure OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="custom">自定义</option>
                      </select>
                    </div>
                    <div>
                      <Label>Base URL</Label>
                      <Input 
                        value={form.base_url} 
                        onChange={(e) => setForm({...form, base_url: e.target.value})}
                        placeholder="https://api.openai.com/v1"
                      />
                    </div>
                    <div className="col-span-2">
                      <Label>API Key {editingId && "(留空则不修改)"}</Label>
                      <div className="flex gap-2">
                        <Input 
                          type={showApiKey ? "text" : "password"}
                          value={form.api_key} 
                          onChange={(e) => setForm({...form, api_key: e.target.value})}
                          placeholder={editingId ? "留空则保持原值" : "sk-xxxxxx"}
                          className="flex-1"
                        />
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="icon"
                          onClick={() => setShowApiKey(!showApiKey)}
                        >
                          {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                    <div className="col-span-2 flex items-center gap-2">
                      <input 
                        type="checkbox"
                        checked={form.enabled}
                        onChange={(e) => setForm({...form, enabled: e.target.checked})}
                        className="rounded"
                      />
                      <Label className="mb-0">启用该模型</Label>
                    </div>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={handleCancel}>
                      <X className="h-4 w-4 mr-1" />
                      取消
                    </Button>
                    <Button onClick={handleSave} disabled={isLoading}>
                      {isLoading ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Save className="h-4 w-4 mr-1" />}
                      保存
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 模型列表 */}
            {isLoading && !models.length ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-3">
                {models.map((model) => (
                  <Card key={model.id} className={!model.enabled ? "opacity-60" : ""}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{model.name}</span>
                            <span className="text-xs bg-muted px-2 py-0.5 rounded">{model.id}</span>
                            {!model.enabled && (
                              <span className="text-xs bg-destructive/20 text-destructive px-2 py-0.5 rounded">已禁用</span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground mt-1 space-y-1">
                            <div>提供商: <span className="text-foreground">{model.provider}</span></div>
                            <div>Base URL: <span className="text-foreground">{model.base_url || "-"}</span></div>
                            <div>API Key: <span className="font-mono text-foreground">{model.api_key_masked || "-"}</span></div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => handleEdit(model)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => handleDelete(model.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {models.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    暂无模型配置，点击"添加模型"开始配置
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

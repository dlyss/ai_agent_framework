import { apiClient } from "./client";
import type { ChatRequest, ChatResponse, ProviderInfo } from "@/types";

export const chatApi = {
  async completions(data: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>("/chat/completions", data);
    return response.data;
  },

  async getModels(): Promise<{ providers: ProviderInfo[] }> {
    const response = await apiClient.get<{ providers: ProviderInfo[] }>("/chat/models");
    return response.data;
  },
};

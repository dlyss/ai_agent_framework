import { apiClient } from "./client";
import type { Document, RAGQueryRequest, RAGQueryResponse, Collection } from "@/types";

export interface UploadDocumentsRequest {
  documents: Document[];
  collection_name: string;
}

export interface UploadDocumentsResponse {
  success: boolean;
  document_ids: string[];
  collection_name: string;
}

export const ragApi = {
  async createCollection(name: string, dimension?: number): Promise<{ success: boolean }> {
    const response = await apiClient.post("/rag/collections", { 
      name, 
      dimension: dimension || 768 
    });
    return response.data;
  },

  async deleteCollection(name: string): Promise<{ success: boolean }> {
    const response = await apiClient.delete(`/rag/collections/${name}`);
    return response.data;
  },

  async uploadDocuments(data: UploadDocumentsRequest): Promise<UploadDocumentsResponse> {
    const response = await apiClient.post<UploadDocumentsResponse>("/rag/documents", data);
    return response.data;
  },

  async query(data: RAGQueryRequest): Promise<RAGQueryResponse> {
    const response = await apiClient.post<RAGQueryResponse>("/rag/query", data);
    return response.data;
  },

  async searchDocuments(
    collectionName: string,
    query: string,
    topK?: number
  ): Promise<{ results: Document[] }> {
    const response = await apiClient.get("/rag/search", {
      params: { collection_name: collectionName, query, top_k: topK },
    });
    return response.data;
  },
};

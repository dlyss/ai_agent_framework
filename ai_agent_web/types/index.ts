export interface User {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  messages: Message[];
  model?: string;
  provider?: string;
  temperature?: number;
  max_tokens?: number;
  session_id?: string;
}

export interface ChatResponse {
  content: string;
  model: string;
  provider: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface Document {
  content: string;
  metadata?: Record<string, unknown>;
}

export interface RAGQueryRequest {
  question: string;
  collection_name: string;
  top_k?: number;
  include_sources?: boolean;
}

export interface RAGQueryResponse {
  answer: string;
  sources?: {
    content: string;
    score: number;
    metadata?: Record<string, unknown>;
  }[];
}

export interface Collection {
  name: string;
  count: number;
  dimension: number;
}

export interface ProviderInfo {
  name: string;
  models: string[];
}

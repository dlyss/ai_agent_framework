import { apiClient } from "./client";
import type { User, Token } from "@/types";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email: string;
}

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

  async refresh(): Promise<Token> {
    const response = await apiClient.post<Token>("/auth/refresh");
    return response.data;
  },
};

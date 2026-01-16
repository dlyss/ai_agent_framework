import { create } from "zustand";
import type { Message } from "@/types";

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sessionId: string;
  model: string;
  provider: string;
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setModel: (model: string) => void;
  setProvider: (provider: string) => void;
  setSessionId: (sessionId: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  sessionId: `session-${Date.now()}`,
  model: "gpt-3.5-turbo",
  provider: "openai",

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages];
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content,
        };
      }
      return { messages };
    }),

  clearMessages: () => set({ messages: [] }),

  setLoading: (isLoading) => set({ isLoading }),

  setModel: (model) => set({ model }),

  setProvider: (provider) => set({ provider }),

  setSessionId: (sessionId) => set({ sessionId }),
}));

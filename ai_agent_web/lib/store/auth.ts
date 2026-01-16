import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Token } from "@/types";
import { authApi } from "@/lib/api/auth";

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: true,

      login: async (username: string, password: string) => {
        const data = await authApi.login({ username, password });
        localStorage.setItem("access_token", data.access_token);
        set({ token: data.access_token });
        await get().fetchUser();
      },

      register: async (username: string, password: string, email: string) => {
        await authApi.register({ username, password, email });
      },

      logout: () => {
        localStorage.removeItem("access_token");
        set({ token: null, user: null });
      },

      fetchUser: async () => {
        try {
          const token = localStorage.getItem("access_token");
          if (!token) {
            set({ isLoading: false });
            return;
          }
          const user = await authApi.getMe();
          set({ user, token, isLoading: false });
        } catch {
          set({ token: null, user: null, isLoading: false });
          localStorage.removeItem("access_token");
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => (state) => {
        state?.fetchUser();
      },
    }
  )
);

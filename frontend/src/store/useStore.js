import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      activeProject: null,

      setAuth: (user, token, refreshToken) => set({ user, token, refreshToken }),
      setTokens: (token, refreshToken) => set({ token, refreshToken }),
      logout: () => set({ user: null, token: null, refreshToken: null, activeProject: null }),
      
      setActiveProject: (project) => set({ activeProject: project }),
    }),
    {
      name: 'buildx-storage', // name of the item in the storage (must be unique)
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token, 
        refreshToken: state.refreshToken 
      }), // only persist auth data
    }
  )
);

export default useStore;

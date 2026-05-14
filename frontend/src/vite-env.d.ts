/// <reference types="vite/client" />

declare module 'vite/client' {
  interface ImportMetaEnv {
    readonly VITE_API_BASE_URL?: string;
    // Add more env variables here as needed
  }
}


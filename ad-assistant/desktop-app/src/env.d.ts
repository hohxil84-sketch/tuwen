/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<object, object, unknown>;
  export default component;
}

/** Custom Vite env vars for this project. */
interface ImportMetaEnv {
  /** Cloud backend API base URL (default: http://127.0.0.1:8000). */
  readonly VITE_CLOUD_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

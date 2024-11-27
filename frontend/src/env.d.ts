/// <reference path="../.astro/types.d.ts" />
interface ImportMetaEnv {
    readonly PUBLIC_API_URL: string;
    // more env variables...
  }
  
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
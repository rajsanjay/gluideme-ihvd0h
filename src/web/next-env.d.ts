/// <reference types="next" />
/// <reference types="next/image-types/global" />

// @next/env version 13.4.0
// next version 13.4.0

// NOTE: This file should not be edited
// see https://nextjs.org/docs/basic-features/typescript for more information

declare namespace NodeJS {
  interface ProcessEnv extends NodeJS.ProcessEnv {
    readonly NEXT_PUBLIC_API_URL: string;
    readonly NEXT_PUBLIC_MEILISEARCH_URL: string;
  }
}

interface ImageConfig {
  deviceSizes: number[];
  imageSizes: number[];
  loader: string;
  path: string;
  domains: string[];
  formats: string[];
}

declare module "*.png" {
  const content: string;
  export default content;
}

declare module "*.jpg" {
  const content: string;
  export default content;
}

declare module "*.jpeg" {
  const content: string;
  export default content;
}

declare module "*.gif" {
  const content: string;
  export default content;
}

declare module "*.webp" {
  const content: string;
  export default content;
}

declare module "*.avif" {
  const content: string;
  export default content;
}

declare module "*.ico" {
  const content: string;
  export default content;
}

declare module "*.bmp" {
  const content: string;
  export default content;
}

declare module "*.svg" {
  const content: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
  export default content;
}
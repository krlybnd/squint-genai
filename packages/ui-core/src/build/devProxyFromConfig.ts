import type { AppConfigDefinition } from "../app/types";

export function devProxyFromConfig(definition: AppConfigDefinition): Record<string, object> {
  const proxy: Record<string, object> = {};
  for (const [path, entry] of Object.entries(definition.devProxy ?? {})) {
    proxy[path] = {
      target: entry.target,
      changeOrigin: entry.changeOrigin ?? true,
      ...(entry.stripPrefix
        ? { rewrite: (requestPath: string) => requestPath.replace(new RegExp(`^${entry.stripPrefix}`), "") }
        : {}),
    };
  }
  return proxy;
}

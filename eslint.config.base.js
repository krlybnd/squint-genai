import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

/** Shared ESLint flat config — extend in each Node project's eslint.config.js */
export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    ignores: [
      "**/dist/**",
      "**/node_modules/**",
      "**/.features-gen/**",
      "**/scripts/**",
      "**/*.mjs",
      "**/src/api/generated/**",
      "**/src/generated/**",
    ],
  },
);

import { defineConfig } from "vite";

// Relative base so the build works at the default GitHub Pages address of any repository name (V-01).
export default defineConfig({ base: "./", build: { outDir: "dist", sourcemap: false } });

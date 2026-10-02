import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // The client view imports the demo scenarios from the repo's data/ folder.
  server: { fs: { allow: [".."] } },
});

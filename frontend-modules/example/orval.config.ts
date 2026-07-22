import { defineConfig } from "@ocelescope/api-config";

// `defineConfig` applies Ocelescope's shared Orval defaults (react-query over
// axios, input ./openapi.json, and the customFetch mutator below). You only
// provide the output target.
export default defineConfig({
  example: {
    output: { target: "./src/api/example.ts" },
  },
});

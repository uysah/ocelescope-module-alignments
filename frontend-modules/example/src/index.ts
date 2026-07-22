import { defineModule, defineModuleRoute } from "@ocelescope/core";
import { SparklesIcon } from "lucide-react";
import Hello from "./routes/Hello";

const helloRoute = defineModuleRoute({
  name: "hello",
  label: "Hello",
  component: Hello,
});

export default defineModule({
  name: "example",
  label: "Example",
  description: "An example custom Ocelescope module",
  authors: [{ name: "Your Name" }],
  icon: SparklesIcon,
  routes: [helloRoute],
});

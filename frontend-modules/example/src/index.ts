import { defineModule, defineModuleRoute } from "@ocelescope/core";
import { SquareCenterlineDashedVertical } from "lucide-react";
import Alignments from "./pages/alignments";

const helloRoute = defineModuleRoute({
  name: "Alignments",
  label: "Alignments",
  component: Alignments,
});

export default defineModule({
  name: "Case-Centric Alignments",
  label: "Alignments",
  description: "Case-Centric Alignments",
  authors: [{ name: "Your Name" }],
  icon: SquareCenterlineDashedVertical,
  routes: [helloRoute],
});

import { defineModule, defineModuleRoute } from "@ocelescope/core";
import { SquareCenterlineDashedVertical } from "lucide-react";
import {objectPageRoute} from "./pages/alignments";

export default defineModule({
  name: "Case-Centric Alignments",
  label: "Alignments",
  description: "Case-Centric Alignments",
  authors: [{ name: "Your Name" }],
  icon: SquareCenterlineDashedVertical,
  routes: [objectPageRoute],
});

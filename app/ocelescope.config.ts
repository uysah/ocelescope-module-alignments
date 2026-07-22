import type { OcelescopeConfig } from "@ocelescope/core";
import management from "@ocelescope/management";
import example from "@instance/example-module";

export default {
	modules: [management, example],
} satisfies OcelescopeConfig;

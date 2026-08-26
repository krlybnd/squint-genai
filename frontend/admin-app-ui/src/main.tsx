import { bootstrapApp } from "@are/ui-core/app/bootstrapApp";
import { appDefinition } from "./app.config";
import { initAppI18n } from "./i18n";
import "@are/ui-core/styles/base.css";
import "./App.css";

void (async () => {
  const i18n = await initAppI18n();
  await bootstrapApp({
    definition: appDefinition,
    i18n,
    loadApp: () => import("./App"),
  });
})();

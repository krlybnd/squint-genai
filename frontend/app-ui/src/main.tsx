import { bootstrapApp } from "@are/ui-core/app/bootstrapApp";
import { appDefinition } from "./app.config";
import i18n from "./i18n";
import "@are/ui-core/styles/base.css";
import "./App.css";

void bootstrapApp({
  definition: appDefinition,
  i18n,
  loadApp: () => import("./App"),
});

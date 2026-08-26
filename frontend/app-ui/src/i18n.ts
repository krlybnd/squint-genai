import { createAppI18nFromLocales } from "@are/ui-core/app/appI18n";
import de from "./locales/de.json";
import en from "./locales/en.json";
import hu from "./locales/hu.json";

export default createAppI18nFromLocales({ en, hu, de });

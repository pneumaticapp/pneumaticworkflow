import { EIntegrations } from "../../../types/integrations";
import { isArrayWithItems } from "../../../utils/helpers";

export function checkShowDraftTemplateWarning(
  isTemplateActive: boolean,
  isTemplatePublic: boolean,
  templateIntegrations: EIntegrations[]
) {
  return !isTemplateActive && (isArrayWithItems(templateIntegrations) || isTemplatePublic);
}

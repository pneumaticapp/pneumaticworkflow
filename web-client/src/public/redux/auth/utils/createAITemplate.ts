import { call } from "redux-saga/effects";
import { getLandingTemplateObject, resetLandingTemplate } from "../../../utils/landingTemplate";
import { createTemplateBySteps } from "../../../api/createTemplateBySteps";

export function* createAITemplate() {
  const template = getLandingTemplateObject();
  if (!template) {
    throw new Error('No template set');
  }

  yield call(createTemplateBySteps, template);
  resetLandingTemplate();
}

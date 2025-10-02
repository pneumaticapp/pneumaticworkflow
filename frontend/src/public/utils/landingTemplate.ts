import { TTemplateWithTasksOnly } from "../types/template";

export const LANDING_TEMPLATE_STORAGE_KEY = 'landing-template';

export function setLandingTemplate(token: string) {
  sessionStorage.setItem(LANDING_TEMPLATE_STORAGE_KEY, token);
}

export function getLandingTemplate() {
  return sessionStorage.getItem(LANDING_TEMPLATE_STORAGE_KEY);
}

export function resetLandingTemplate() {
  sessionStorage.removeItem(LANDING_TEMPLATE_STORAGE_KEY);
}

export function getLandingTemplateObject(): TTemplateWithTasksOnly | null {
  const templateString = getLandingTemplate();
  if (!templateString) {
    return null;
  }

  try {
    const template = JSON.parse(templateString);

    if (typeof template === 'object') {
      return template as TTemplateWithTasksOnly;
    }

    return null;
  } catch (error) {
    return null;
  }
}

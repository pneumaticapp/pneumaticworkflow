export const TEMPLATE_NAME_STORAGE_KEY = 'template-name';

export function setTemplateName(name: string) {
  sessionStorage.setItem(TEMPLATE_NAME_STORAGE_KEY, name);
}

export function getTemplateName() {
  return sessionStorage.getItem(TEMPLATE_NAME_STORAGE_KEY);
}

export function resetTemplateName() {
  sessionStorage.removeItem(TEMPLATE_NAME_STORAGE_KEY);
}

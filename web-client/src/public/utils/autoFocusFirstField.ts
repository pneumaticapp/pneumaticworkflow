export function autoFocusFirstField(fieldsContainer: HTMLElement | null) {
  if (!fieldsContainer) {
    return;
  }

  const firstAutoFocusContainer =
    fieldsContainer?.querySelector('[data-autofocus-first-field="true"], [data-autofocus-first-field="true"]');

  if (!firstAutoFocusContainer) {
    return;
  }

  const fieldToFocus = firstAutoFocusContainer.querySelector<
  HTMLTextAreaElement | HTMLInputElement
  >('input:enabled, textarea:enabled');

  if (fieldToFocus) {
    fieldToFocus.focus();
  }
}

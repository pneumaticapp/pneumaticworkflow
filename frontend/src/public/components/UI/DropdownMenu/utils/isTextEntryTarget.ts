export const isTextEntryTarget = (target: EventTarget) =>
  target instanceof Element &&
  Boolean(target.closest('input, textarea, [contenteditable]:not([contenteditable="false"])'));

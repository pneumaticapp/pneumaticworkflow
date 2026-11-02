export function moveMenuItemFocus(container: HTMLElement, step: 1 | -1) {
  const items = Array.from(container.querySelectorAll<HTMLElement>('[role="menuitem"]')).filter(
    (item) => !item.closest('[aria-hidden="true"]'),
  );
  if (!items.length) return;

  const currentIndex = items.findIndex((item) => item === document.activeElement);
  const startIndex = step === 1 ? -1 : 0;
  const nextIndex = ((currentIndex === -1 ? startIndex : currentIndex) + step + items.length) % items.length;
  items[nextIndex].focus();
}

/**
 * Collects scrollable ancestors (overflow: auto | scroll) from the given element up to body.
 * Used for link form positioning and scroll-snapshot restoration.
 */
export function findScrollableElements(from: Element): Element[] {
  const result: Element[] = [];
  let current: Element | null = from;
  while (current && current !== document.body) {
    const style = window.getComputedStyle(current);
    const scrollable =
      style.overflow === 'auto' ||
      style.overflow === 'scroll' ||
      style.overflowX === 'auto' ||
      style.overflowX === 'scroll' ||
      style.overflowY === 'auto' ||
      style.overflowY === 'scroll';
    if (scrollable) result.push(current);
    current = current.parentElement;
  }
  return result;
}

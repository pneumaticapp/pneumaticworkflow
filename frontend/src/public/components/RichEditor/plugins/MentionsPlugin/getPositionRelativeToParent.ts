export function getPositionRelativeToParent(
  element: HTMLElement | null,
  rect: DOMRect,
  gap = 4,
): { top: number; left: number } {
  const parent = element?.offsetParent as HTMLElement | null;
  if (!parent) {
    return { top: rect.bottom + gap, left: rect.left };
  }

  const parentRect = parent.getBoundingClientRect();

  return {
    top: rect.bottom - parentRect.top + gap,
    left: rect.left - parentRect.left,
  };
}

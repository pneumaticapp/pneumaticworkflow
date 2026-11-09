export function getPositionRelativeToParent(
  element: HTMLElement | null,
  rect: DOMRect,
  gap = 4,
  direction: 'ltr' | 'rtl' = 'ltr',
): { top: number; left: number } {
  const width = element?.offsetWidth ?? 0;
  const height = element?.offsetHeight ?? 0;
  const edgeGap = 8;
  const anchorLeft = direction === 'rtl' ? rect.right - width : rect.left;
  const left = width ? Math.max(edgeGap, Math.min(anchorLeft, window.innerWidth - width - edgeGap)) : anchorLeft;
  let top = rect.bottom + gap;

  if (height && top + height > window.innerHeight - edgeGap) {
    const above = rect.top - height - gap;
    top = above >= edgeGap ? above : Math.max(edgeGap, window.innerHeight - height - edgeGap);
  }

  const parent = element?.offsetParent as HTMLElement | null;
  if (!parent) {
    return { top: top + window.scrollY, left: left + window.scrollX };
  }

  const parentRect = parent.getBoundingClientRect();

  return {
    top: top - parentRect.top - parent.clientTop + parent.scrollTop,
    // These are physical CSS coordinates. Signed RTL scrollLeft is intentional.
    left: left - parentRect.left - parent.clientLeft + parent.scrollLeft,
  };
}

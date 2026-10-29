import type { TSubmenuPlacement } from '../types';

export function getSubmenuPlacement(rowRect: DOMRect, panelWidth: number, viewportWidth: number): TSubmenuPlacement {
  if (rowRect.right + panelWidth <= viewportWidth) return { side: 'right' };
  if (rowRect.left - panelWidth >= 0) return { side: 'left' };

  return { side: 'shifted', left: Math.max(0, viewportWidth - panelWidth) - rowRect.left };
}

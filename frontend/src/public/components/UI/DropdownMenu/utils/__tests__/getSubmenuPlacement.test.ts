import { getSubmenuPlacement } from '../getSubmenuPlacement';

const rowRect = (left: number, right: number) => ({ left, right }) as DOMRect;

describe('getSubmenuPlacement', () => {
  it('keeps the submenu on the right when it fits', () => {
    expect(getSubmenuPlacement(rowRect(100, 300), 200, 1000)).toEqual({ side: 'right' });
  });

  it('flips the submenu to the left when only the left side fits', () => {
    expect(getSubmenuPlacement(rowRect(600, 900), 304, 1000)).toEqual({ side: 'left' });
  });

  it('shifts the submenu into the window when neither side fits', () => {
    expect(getSubmenuPlacement(rowRect(40, 340), 304, 375)).toEqual({ side: 'shifted', left: 31 });
  });

  it('pins a submenu wider than the window to its left edge', () => {
    expect(getSubmenuPlacement(rowRect(40, 340), 496, 375)).toEqual({ side: 'shifted', left: -40 });
  });
});

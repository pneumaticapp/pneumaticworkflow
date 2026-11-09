import { getPositionRelativeToParent } from '../getPositionRelativeToParent';

const rect = (left: number, top: number, width: number, height: number): DOMRect =>
  ({ left, top, right: left + width, bottom: top + height, width, height }) as DOMRect;

describe('mention menu physical coordinates', () => {
  const parent = document.createElement('div');
  const menu = document.createElement('div');

  beforeEach(() => {
    jest.spyOn(parent, 'getBoundingClientRect').mockReturnValue(rect(100, 80, 400, 300));
    Object.defineProperties(parent, {
      clientLeft: { configurable: true, value: 18 },
      clientTop: { configurable: true, value: 2 },
      scrollLeft: { configurable: true, value: -60 },
      scrollTop: { configurable: true, value: 30 },
    });
    Object.defineProperties(menu, {
      offsetParent: { configurable: true, value: parent },
      offsetWidth: { configurable: true, value: 192 },
      offsetHeight: { configurable: true, value: 100 },
    });
  });

  afterEach(() => jest.restoreAllMocks());

  it('aligns the inline start in RTL and accounts for border, scrollbar, and signed scrolling', () => {
    const anchor = rect(300, 140, 40, 20);
    const position = getPositionRelativeToParent(menu, anchor, 4, 'rtl');

    // Translate the CSS left coordinate back to viewport space.
    expect(100 + 18 + position.left - parent.scrollLeft + menu.offsetWidth).toBe(anchor.right);
    expect(80 + 2 + position.top - parent.scrollTop).toBe(anchor.bottom + 4);
  });

  it('preserves leading alignment for LTR', () => {
    const anchor = rect(300, 140, 40, 20);
    const position = getPositionRelativeToParent(menu, anchor, 4, 'ltr');
    expect(100 + 18 + position.left - parent.scrollLeft).toBe(anchor.left);
  });

  it('keeps a menu at the viewport edge visible', () => {
    const anchor = rect(4, 140, 10, 20);
    const position = getPositionRelativeToParent(menu, anchor, 4, 'rtl');
    expect(100 + 18 + position.left - parent.scrollLeft).toBe(8);
  });

  it('opens above the anchor when the bottom of the viewport has no space', () => {
    const anchor = rect(300, window.innerHeight - 30, 40, 20);
    const position = getPositionRelativeToParent(menu, anchor, 4, 'rtl');
    expect(80 + 2 + position.top - parent.scrollTop + menu.offsetHeight).toBe(anchor.top - 4);
  });
});

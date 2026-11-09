import { createResizeHandler } from '../resizeUtils';

describe('workflow table column resizing', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(window, 'requestAnimationFrame').mockImplementation((callback) => {
      callback(0);
      return 1;
    });
    localStorage.clear();
  });

  afterEach(() => {
    document.dispatchEvent(new MouseEvent('mouseup'));
    jest.runOnlyPendingTimers();
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  it.each([
    ['ltr', 550, 250],
    ['ltr', 350, 100],
    ['rtl', 450, 250],
    ['rtl', 650, 100],
  ])('resizes in %s at x=%i while honoring minimum width', (direction, clientX, expected) => {
    const handle = document.createElement('span');
    handle.style.direction = direction;
    let widths: Record<string, number> = { 'system-column-workflow': 200 };
    const setWidths = jest.fn((update) => {
      widths = typeof update === 'function' ? update(widths) : update;
    });
    const startResize = createResizeHandler(widths, setWidths, 12, 7);

    startResize({ clientX: 500, currentTarget: handle } as unknown as React.MouseEvent, 'system-column-workflow', 100);
    document.dispatchEvent(new MouseEvent('mousemove', { clientX }));

    expect(widths['system-column-workflow']).toBe(expected);
    document.dispatchEvent(new MouseEvent('mouseup'));
    jest.runOnlyPendingTimers();
    expect(JSON.parse(localStorage.getItem('workflow-column-widths-12-global')!)).toEqual({
      'system-column-workflow': expected,
    });

    document.dispatchEvent(new MouseEvent('mousemove', { clientX: 700 }));
    expect(setWidths).toHaveBeenCalledTimes(1);
  });
});

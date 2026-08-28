import {
  getNavbarOffset,
  getScrollParent,
  getScrollTargetTop,
  scrollToElement,
  scrollToElementWhenStable,
} from '../scroll';

type TRectOverrides = { top: number };

const setRect = (node: HTMLElement, { top }: TRectOverrides) => {
  node.getBoundingClientRect = jest.fn(() => ({ top } as DOMRect));
};

const setBox = (node: HTMLElement, { scrollHeight, clientHeight }: { scrollHeight: number; clientHeight: number }) => {
  Object.defineProperty(node, 'scrollHeight', { value: scrollHeight, configurable: true });
  Object.defineProperty(node, 'clientHeight', { value: clientHeight, configurable: true });
};

const mockOverflow = (overflowMap: Map<HTMLElement, string>) => {
  jest
    .spyOn(window, 'getComputedStyle')
    .mockImplementation((node) => ({ overflowY: overflowMap.get(node as HTMLElement) || 'visible' } as CSSStyleDeclaration));
};

const setWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
};

const buildTree = () => {
  const container = document.createElement('div');
  const inner = document.createElement('div');
  const element = document.createElement('div');

  container.appendChild(inner);
  inner.appendChild(element);
  document.body.appendChild(container);

  container.scrollTo = jest.fn();
  setBox(container, { scrollHeight: 5000, clientHeight: 800 });
  setRect(container, { top: 0 });

  return { container, inner, element };
};

describe('scroll utils', () => {
  let frames: FrameRequestCallback[] = [];

  const flushFrame = () => {
    const pending = frames;
    frames = [];
    pending.forEach((frame) => frame(0));
  };

  beforeEach(() => {
    frames = [];
    document.body.innerHTML = '';
    setWindowWidth(1200);

    window.requestAnimationFrame = jest.fn((callback: FrameRequestCallback) => {
      frames.push(callback);

      return frames.length;
    });
    window.cancelAnimationFrame = jest.fn();
    window.scrollTo = jest.fn();
    setRect(document.body, { top: 0 });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  describe('getNavbarOffset', () => {
    it('insets by the navbar height on desktop', () => {
      setWindowWidth(1200);

      expect(getNavbarOffset()).toBe(104);
    });

    it('does not inset on mobile, where the navbar is not sticky', () => {
      setWindowWidth(500);

      expect(getNavbarOffset()).toBe(0);
    });
  });

  describe('getScrollParent', () => {
    it('returns the nearest ancestor that actually scrolls', () => {
      const { container, element } = buildTree();
      mockOverflow(new Map([[container, 'scroll']]));

      expect(getScrollParent(element)).toBe(container);
    });

    it('skips a scrollable ancestor that has nothing to scroll', () => {
      const { container, element } = buildTree();
      setBox(container, { scrollHeight: 800, clientHeight: 800 });
      mockOverflow(new Map([[container, 'scroll']]));

      expect(getScrollParent(element)).toBeNull();
    });

    it('skips ancestors whose overflow is toggled off', () => {
      const { container, element } = buildTree();
      mockOverflow(new Map([[container, 'hidden']]));

      expect(getScrollParent(element)).toBeNull();
    });

    it('returns null when nothing between the element and body scrolls', () => {
      const { element } = buildTree();
      mockOverflow(new Map());

      expect(getScrollParent(element)).toBeNull();
    });
  });

  describe('getScrollTargetTop', () => {
    it('offsets the element against the container scroll position', () => {
      const { container, element } = buildTree();
      setRect(container, { top: 100 });
      setRect(element, { top: 900 });
      Object.defineProperty(container, 'scrollTop', { value: 300, configurable: true });

      expect(getScrollTargetTop(element, container, 104)).toBe(996);
    });

    it('ignores body padding, which the container geometry already accounts for', () => {
      const { container, element } = buildTree();
      document.body.style.paddingTop = '40px';
      setRect(container, { top: 0 });
      setRect(element, { top: 500 });
      Object.defineProperty(container, 'scrollTop', { value: 0, configurable: true });

      expect(getScrollTargetTop(element, container, 104)).toBe(396);
    });

    it('clamps to the top when the target sits above the container', () => {
      const { container, element } = buildTree();
      setRect(container, { top: 0 });
      setRect(element, { top: 10 });
      Object.defineProperty(container, 'scrollTop', { value: 0, configurable: true });

      expect(getScrollTargetTop(element, container, 104)).toBe(0);
    });

    it('clamps to the maximum reachable offset for the last section on the page', () => {
      const { container, element } = buildTree();
      setBox(container, { scrollHeight: 1000, clientHeight: 800 });
      setRect(container, { top: 0 });
      setRect(element, { top: 950 });
      Object.defineProperty(container, 'scrollTop', { value: 0, configurable: true });

      expect(getScrollTargetTop(element, container, 104)).toBe(200);
    });
  });

  describe('scrollToElement', () => {
    it('scrolls the container rather than the window', () => {
      const { container, element } = buildTree();
      mockOverflow(new Map([[container, 'scroll']]));
      setRect(container, { top: 0 });
      setRect(element, { top: 904 });
      Object.defineProperty(container, 'scrollTop', { value: 0, configurable: true });

      scrollToElement(element);
      flushFrame();

      expect(container.scrollTo).toHaveBeenCalledWith({ top: 800, left: 0, behavior: 'smooth' });
      expect(window.scrollTo).not.toHaveBeenCalled();
    });

    it('falls back to the window when no ancestor scrolls', () => {
      const { element } = buildTree();
      mockOverflow(new Map());
      setRect(element, { top: 604 });
      Object.defineProperty(document.documentElement, 'scrollHeight', { value: 5000, configurable: true });
      Object.defineProperty(document.documentElement, 'clientHeight', { value: 800, configurable: true });

      scrollToElement(element);
      flushFrame();

      expect(window.scrollTo).toHaveBeenCalledWith({ top: 500, left: 0, behavior: 'smooth' });
    });

    it('defers the scroll by the given delay', () => {
      // modern fake timers also replace requestAnimationFrame, so re-install the stub after enabling them
      jest.useFakeTimers();
      window.requestAnimationFrame = jest.fn((callback: FrameRequestCallback) => {
        frames.push(callback);

        return frames.length;
      });

      const { container, element } = buildTree();
      mockOverflow(new Map([[container, 'scroll']]));
      setRect(element, { top: 104 });
      Object.defineProperty(container, 'scrollTop', { value: 0, configurable: true });

      scrollToElement(element, 300);
      flushFrame();

      expect(container.scrollTo).not.toHaveBeenCalled();

      jest.advanceTimersByTime(300);

      expect(container.scrollTo).toHaveBeenCalledTimes(1);
    });
  });

  describe('scrollToElementWhenStable', () => {
    const setUp = (tops: number[]) => {
      const { container, element } = buildTree();
      mockOverflow(new Map([[container, 'scroll']]));
      setRect(container, { top: 0 });
      Object.defineProperty(container, 'scrollTop', { value: 0, configurable: true });

      let index = 0;
      element.getBoundingClientRect = jest.fn(() => {
        const top = tops[Math.min(index, tops.length - 1)];
        index += 1;

        return { top } as DOMRect;
      });

      return { container, element };
    };

    it('waits for the moving target to settle before scrolling once', () => {
      const { container, element } = setUp([604, 804, 1004, 1004, 1004, 1004]);

      scrollToElementWhenStable(element);

      flushFrame();
      flushFrame();
      flushFrame();
      expect(container.scrollTo).not.toHaveBeenCalled();

      flushFrame();
      flushFrame();

      expect(container.scrollTo).toHaveBeenCalledTimes(1);
      expect(container.scrollTo).toHaveBeenCalledWith({ top: 900, left: 0, behavior: 'smooth' });
    });

    it('corrects once, without animation, when late content shifts the target', () => {
      const { container, element } = setUp([604, 604, 604, 604, 1204]);

      scrollToElementWhenStable(element);

      flushFrame();
      flushFrame();
      flushFrame();
      expect(container.scrollTo).toHaveBeenCalledWith({ top: 500, left: 0, behavior: 'smooth' });

      flushFrame();
      flushFrame();

      expect(container.scrollTo).toHaveBeenLastCalledWith({ top: 1100, left: 0, behavior: 'auto' });
      expect(container.scrollTo).toHaveBeenCalledTimes(2);
    });

    it('ignores sub-pixel drift below the threshold', () => {
      const { container, element } = setUp([604, 604, 604, 604, 606]);

      scrollToElementWhenStable(element);

      flushFrame();
      flushFrame();
      flushFrame();
      flushFrame();
      flushFrame();

      expect(container.scrollTo).toHaveBeenCalledTimes(1);
    });

    it('scrolls anyway once the settle window expires on never-stable content', () => {
      const nowSpy = jest.spyOn(Date, 'now');
      nowSpy.mockReturnValueOnce(0).mockReturnValue(1000);

      const { container, element } = setUp([604, 804, 1004, 1204]);

      scrollToElementWhenStable(element, { settleTimeout: 250, timeout: 2000 });
      flushFrame();

      expect(container.scrollTo).toHaveBeenCalledTimes(1);
    });

    it('stops on cancel', () => {
      const { container, element } = setUp([604]);

      const cancel = scrollToElementWhenStable(element);
      cancel();
      flushFrame();
      flushFrame();
      flushFrame();

      expect(container.scrollTo).not.toHaveBeenCalled();
    });

    it('aborts as soon as the user scrolls', () => {
      const { container, element } = setUp([604, 804, 1004, 1004, 1004]);

      scrollToElementWhenStable(element);
      flushFrame();

      window.dispatchEvent(new Event('wheel'));

      flushFrame();
      flushFrame();
      flushFrame();

      expect(container.scrollTo).not.toHaveBeenCalled();
    });
  });
});

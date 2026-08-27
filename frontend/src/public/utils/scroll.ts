import { NAVBAR_HEIGHT, MOBILE_NAVBAR_HEIGHT } from '../constants/defaultValues';

const { MOBILE_MAX_WIDTH_BREAKPOINT } = require('../constants/breakpoints');

export type TScrollBehavior = 'auto' | 'smooth';

const SCROLLABLE_OVERFLOW = ['auto', 'scroll', 'overlay'];

/**
 * The app does not scroll the window: MainLayout renders #app-container with
 * `overflow: scroll; height: 100%`, so the document itself never overflows.
 * Every scroll helper has to target the nearest scrolling ancestor instead.
 */
export const getScrollParent = (element: HTMLElement): HTMLElement | null => {
  let current = element.parentElement;

  while (current && current !== document.body) {
    const { overflowY } = window.getComputedStyle(current);

    if (SCROLLABLE_OVERFLOW.includes(overflowY) && current.scrollHeight > current.clientHeight) {
      return current;
    }

    current = current.parentElement;
  }

  return null;
};

export const getNavbarOffset = (): number => {
  return window.innerWidth > MOBILE_MAX_WIDTH_BREAKPOINT ? NAVBAR_HEIGHT : MOBILE_NAVBAR_HEIGHT;
};

const clampScrollTop = (value: number, maxValue: number) => Math.max(0, Math.min(value, maxValue));

export const getScrollTargetTop = (
  element: HTMLElement,
  container: HTMLElement | null,
  topOffset: number = getNavbarOffset(),
): number => {
  const elementTop = element.getBoundingClientRect().top;

  if (container) {
    const target =
      elementTop - container.getBoundingClientRect().top - container.clientTop + container.scrollTop - topOffset;

    return clampScrollTop(target, container.scrollHeight - container.clientHeight);
  }

  const scroller = document.scrollingElement || document.documentElement;
  const target = elementTop - document.body.getBoundingClientRect().top - topOffset;

  return clampScrollTop(target, scroller.scrollHeight - scroller.clientHeight);
};

const scrollContainerTo = (container: HTMLElement | null, top: number, behavior: TScrollBehavior) => {
  if (container) {
    container.scrollTo({ top, left: 0, behavior });

    return;
  }

  window.scrollTo({ top, left: 0, behavior });
};

export const scrollToElement = (
  element: HTMLElement,
  delay: number | null = null,
  behavior: TScrollBehavior = 'smooth',
) => {
  window.requestAnimationFrame(() => {
    const scroll = () => {
      const container = getScrollParent(element);

      scrollContainerTo(container, getScrollTargetTop(element, container), behavior);
    };

    if (delay) {
      setTimeout(scroll, delay);

      return;
    }

    scroll();
  });
};

export type TScrollWhenStableOptions = {
  behavior?: TScrollBehavior;
  topOffset?: number;
  timeout?: number;
  settleFrames?: number;
  settleTimeout?: number;
  driftThreshold?: number;
};

const SETTLE_FRAMES = 2;
const SETTLE_TIMEOUT = 250;
const SCROLL_TIMEOUT = 2000;
const DRIFT_THRESHOLD = 4;
const STABLE_TOLERANCE = 1;
const ABORT_EVENTS = ['wheel', 'touchstart', 'keydown'];

/**
 * Scrolls to an element whose position is still moving: an accordion is expanding,
 * lazy data is arriving, third party embeds are mounting. Waits for the target to
 * settle, scrolls once, then corrects a single time if late content shifts it.
 * Returns a cancel function; aborts on any user scroll input.
 */
export const scrollToElementWhenStable = (element: HTMLElement, options: TScrollWhenStableOptions = {}) => {
  const {
    behavior = 'smooth',
    topOffset,
    timeout = SCROLL_TIMEOUT,
    settleFrames = SETTLE_FRAMES,
    settleTimeout = SETTLE_TIMEOUT,
    driftThreshold = DRIFT_THRESHOLD,
  } = options;

  const startedAt = Date.now();

  let frameId: number | null = null;
  let stableFrames = 0;
  let previousTop: number | null = null;
  let scrolledTop: number | null = null;
  let isCancelled = false;

  const cancel = () => {
    if (isCancelled) {
      return;
    }

    isCancelled = true;

    if (frameId !== null) {
      window.cancelAnimationFrame(frameId);
      frameId = null;
    }

    ABORT_EVENTS.forEach((eventName) => window.removeEventListener(eventName, cancel));
  };

  const scroll = (top: number, scrollBehavior: TScrollBehavior) => {
    scrolledTop = top;
    scrollContainerTo(getScrollParent(element), top, scrollBehavior);
  };

  const tick = () => {
    if (isCancelled) {
      return;
    }

    const container = getScrollParent(element);
    const top = getScrollTargetTop(element, container, topOffset);
    const elapsed = Date.now() - startedAt;

    if (scrolledTop === null) {
      stableFrames = previousTop !== null && Math.abs(top - previousTop) <= STABLE_TOLERANCE ? stableFrames + 1 : 0;
      previousTop = top;

      if (stableFrames >= settleFrames || elapsed >= settleTimeout || elapsed >= timeout) {
        scroll(top, behavior);
      }
    } else if (Math.abs(top - scrolledTop) > driftThreshold) {
      scroll(top, 'auto');
      cancel();

      return;
    }

    if (elapsed >= timeout && scrolledTop !== null) {
      cancel();

      return;
    }

    frameId = window.requestAnimationFrame(tick);
  };

  ABORT_EVENTS.forEach((eventName) => window.addEventListener(eventName, cancel, { passive: true }));
  frameId = window.requestAnimationFrame(tick);

  return cancel;
};

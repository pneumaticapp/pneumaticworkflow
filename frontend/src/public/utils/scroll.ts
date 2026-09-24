import { NAVBAR_HEIGHT, MOBILE_NAVBAR_HEIGHT } from '../constants/defaultValues';

const { MOBILE_MAX_WIDTH_BREAKPOINT } = require('../constants/breakpoints');

export type TScrollBehavior = 'auto' | 'smooth';

const SCROLLABLE_OVERFLOW = ['auto', 'scroll', 'overlay'];

// The app scrolls inside #app-container, so window scrolling never applies.
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

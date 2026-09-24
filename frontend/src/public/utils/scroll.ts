import { NAVBAR_HEIGHT, MOBILE_NAVBAR_HEIGHT } from '../constants/defaultValues';

const { MOBILE_MAX_WIDTH_BREAKPOINT } = require('../constants/breakpoints');

export const scrollToElement = (
  element: HTMLElement,
  delay: number | null = null,
  behavior: 'auto' | 'smooth' = 'smooth',
) => {
  window.requestAnimationFrame(() => {
    const elementTopOffset = window.innerWidth > MOBILE_MAX_WIDTH_BREAKPOINT ? NAVBAR_HEIGHT : MOBILE_NAVBAR_HEIGHT;

    let offset = element.offsetTop - elementTopOffset;

    try {
      const bodyRect = document.body.getBoundingClientRect();
      const bodyStyle = window.getComputedStyle(document.body, null);

      // need to handle the padding for the top of the body
      const paddingTop = parseFloat(bodyStyle.getPropertyValue('padding-top'));

      const elementRect = element.getBoundingClientRect();
      offset = elementRect.top - paddingTop - bodyRect.top - elementTopOffset;
    } catch (err) {
      element.scrollIntoView({ behavior });

      return;
    }

    if (delay) {
      setTimeout(() => {
        window.scrollTo({ top: offset, left: 0, behavior });
      }, delay);
    } else {
      window.scrollTo({ top: offset, left: 0, behavior });
    }
  });
};

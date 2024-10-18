const { MOBILE_MAX_WIDTH_BREAKPOINT, DESKTOP_MIN_WIDTH_BREAKPOINT } = require('../constants/breakpoints');

export const isDesktop = () => {
  return window.innerWidth >= DESKTOP_MIN_WIDTH_BREAKPOINT;
}

export const isMobile = () => {
  return window.innerWidth <= MOBILE_MAX_WIDTH_BREAKPOINT;
}

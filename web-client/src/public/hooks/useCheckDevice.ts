/* eslint-disable */
/* prettier-ignore */
import { useMediaQuery } from 'react-responsive';
const { MOBILE_MAX_WIDTH_BREAKPOINT, DESKTOP_MIN_WIDTH_BREAKPOINT } = require('../constants/breakpoints');

interface IUseCheckIsMobileResult {
  isMobile: boolean;
  isDesktop: boolean;
}

export function useCheckDevice(): IUseCheckIsMobileResult {
  const isMobile = useMediaQuery({ query: `(max-width: ${MOBILE_MAX_WIDTH_BREAKPOINT}px)` });
  const isDesktop = useMediaQuery({ query: `(min-width: ${DESKTOP_MIN_WIDTH_BREAKPOINT}px)` });

  return { isMobile, isDesktop };
}

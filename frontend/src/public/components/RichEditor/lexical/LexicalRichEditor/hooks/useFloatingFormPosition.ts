import { useCallback, useEffect, useLayoutEffect, useState } from 'react';

const DEFAULT_OFFSET_PX = 10;
const VIEWPORT_EDGE_PX = 10;

function findScrollableElements(element: Element): Element[] {
  const result: Element[] = [];
  let current: Element | null = element;
  while (current && current !== document.body) {
    const style = window.getComputedStyle(current);
    const scrollable =
      style.overflow === 'auto' ||
      style.overflow === 'scroll' ||
      style.overflowX === 'auto' ||
      style.overflowX === 'scroll' ||
      style.overflowY === 'auto' ||
      style.overflowY === 'scroll';
    if (scrollable) result.push(current);
    current = current.parentElement;
  }
  return result;
}

function getAnchorRect(
  getAnchorRectFn: (() => DOMRect | null) | null | undefined,
  anchorElement: HTMLElement | null | undefined,
): DOMRect | null {
  const rect = getAnchorRectFn?.() ?? null;
  if (rect) return rect;
  return anchorElement ? anchorElement.getBoundingClientRect() : null;
}

function computePositionInContainer(
  anchorRect: DOMRect,
  container: HTMLElement,
  formHeight: number,
  offsetPx: number,
): { top: number; left: number } {
  const containerRect = container.getBoundingClientRect();
  const paddingTop = containerRect.top + (container.clientTop || 0);
  const paddingLeft = containerRect.left + (container.clientLeft || 0);
  const relLeft = anchorRect.left - paddingLeft;
  const relTop = anchorRect.top - paddingTop;
  return {
    left: relLeft + anchorRect.width / 2,
    top: relTop - formHeight - offsetPx,
  };
}

function computePositionInViewport(
  anchorRect: DOMRect,
  formHeight: number,
  formWidth: number,
  offsetPx: number,
): { top: number; left: number } {
  let left = anchorRect.left + anchorRect.width / 2;
  let top = anchorRect.top - formHeight - offsetPx;
  const { innerWidth: vw, innerHeight: vh } = window;

  if (left + formWidth / 2 > vw) left = vw - formWidth / 2 - VIEWPORT_EDGE_PX;
  if (left - formWidth / 2 < 0) left = formWidth / 2 + VIEWPORT_EDGE_PX;
  if (top < VIEWPORT_EDGE_PX) top = VIEWPORT_EDGE_PX;
  if (top + formHeight > vh) top = vh - formHeight - VIEWPORT_EDGE_PX;

  return { top, left };
}

export interface IUseFloatingFormPositionOptions {
  anchorElement?: HTMLElement | null;
  containerRef?: React.RefObject<HTMLElement | null>;
  getAnchorRect?: (() => DOMRect | null) | null;
  isVisible: boolean;
  offsetPx?: number;
}

export interface IFloatingFormPosition {
  top: number;
  left: number;
}

export type TFloatingFormPositionMode = 'fixed' | 'absolute';

export interface IUseFloatingFormPositionResult {
  position: IFloatingFormPosition | null;
  positionMode: TFloatingFormPositionMode;
}


export function useFloatingFormPosition(
  formRef: React.RefObject<HTMLElement | null>,
  options: IUseFloatingFormPositionOptions,
): IUseFloatingFormPositionResult {
  const {
    anchorElement,
    containerRef,
    getAnchorRect: getAnchorRectFn,
    isVisible,
    offsetPx = DEFAULT_OFFSET_PX,
  } = options;

  const [result, setResult] = useState<IUseFloatingFormPositionResult>({
    position: null,
    positionMode: 'fixed',
  });

  const updatePosition = useCallback(() => {
    if (!isVisible || !formRef.current) {
      setResult({ position: null, positionMode: 'fixed' });
      return;
    }

    const anchorRect = getAnchorRect(getAnchorRectFn, anchorElement);
    if (!anchorRect) {
      setResult({ position: null, positionMode: 'fixed' });
      return;
    }

    const { offsetHeight, offsetWidth } = formRef.current;
    const container = containerRef?.current;

    if (container) {
      const position = computePositionInContainer(
        anchorRect,
        container,
        offsetHeight,
        offsetPx,
      );
      setResult({ position, positionMode: 'absolute' });
    } else {
      const position = computePositionInViewport(
        anchorRect,
        offsetHeight,
        offsetWidth,
        offsetPx,
      );
      setResult({ position, positionMode: 'fixed' });
    }
  }, [isVisible, getAnchorRectFn, anchorElement, containerRef, offsetPx, formRef]);

  useLayoutEffect(() => {
    updatePosition();
  }, [updatePosition]);

  useEffect((): (() => void) | undefined => {
    if (!isVisible) return undefined;

    let ticking = false;
    const handleScrollOrResize = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          updatePosition();
          ticking = false;
        });
        ticking = true;
      }
    };

    const scrollable = anchorElement ? findScrollableElements(anchorElement) : [];
    window.addEventListener('scroll', handleScrollOrResize, true);
    window.addEventListener('resize', handleScrollOrResize);
    scrollable.forEach(el => el.addEventListener('scroll', handleScrollOrResize, true));

    return () => {
      window.removeEventListener('scroll', handleScrollOrResize, true);
      window.removeEventListener('resize', handleScrollOrResize);
      scrollable.forEach(el => el.removeEventListener('scroll', handleScrollOrResize, true));
    };
  }, [isVisible, updatePosition, anchorElement]);

  return result;
}

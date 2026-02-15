import { useState, useCallback } from 'react';
import type { ILinkFormState, TLinkFormMode, IScrollSnapshot } from '../plugins/LinkPlugin/types';

function findScrollableElements(from: Element): Element[] {
  const result: Element[] = [];
  let current: Element | null = from;
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

function captureScrollSnapshots(from: Element): IScrollSnapshot[] {
  return findScrollableElements(from).map(el => ({
    element: el,
    scrollLeft: el.scrollLeft,
    scrollTop: el.scrollTop,
  }));
}

function getSelectionContainer(range: Range): Element | null {
  const node = range.startContainer;
  return node.nodeType === Node.ELEMENT_NODE
    ? (node as Element)
    : node.parentElement;
}

function buildScrollAdjustedRect(
  frozenRect: DOMRect,
  windowScroll: { x: number; y: number },
  scrollSnapshots: IScrollSnapshot[],
): DOMRect {
  const { dx, dy } = scrollSnapshots.reduce(
    (acc, { element, scrollLeft, scrollTop }) => ({
      dx: acc.dx + (element.scrollLeft - scrollLeft),
      dy: acc.dy + (element.scrollTop - scrollTop),
    }),
    { dx: window.scrollX - windowScroll.x, dy: window.scrollY - windowScroll.y },
  );
  return new DOMRect(
    frozenRect.left - dx,
    frozenRect.top - dy,
    frozenRect.width,
    frozenRect.height,
  );
}

function rectFromRect(r: DOMRect): DOMRect {
  return new DOMRect(r.left, r.top, r.width, r.height);
}

interface ISelectionAnchorResult {
  frozenRect: DOMRect | null;
  scrollSnapshots: IScrollSnapshot[];
  anchorElement: HTMLElement | null;
}

function captureSelectionAnchor(fallbackRect: DOMRect | null): ISelectionAnchorResult {
  const empty: ISelectionAnchorResult = {
    frozenRect: fallbackRect ? rectFromRect(fallbackRect) : null,
    scrollSnapshots: [],
    anchorElement: null,
  };
  const selection = window.getSelection();
  if (!selection?.rangeCount || selection.isCollapsed) return empty;

  const range = selection.getRangeAt(0);
  const r = range.getBoundingClientRect();
  if (r.width <= 0 && r.height <= 0) return empty;

  const startEl = getSelectionContainer(range);
  const scrollSnapshots = startEl ? captureScrollSnapshots(startEl) : [];
  const anchorElement = startEl ? (startEl as HTMLElement) : null;

  return {
    frozenRect: rectFromRect(r),
    scrollSnapshots,
    anchorElement,
  };
}

function captureButtonAnchor(
  buttonRef: React.RefObject<HTMLButtonElement | null>,
  fallbackRect: DOMRect | null,
): DOMRect | null {
  const source = buttonRef?.current?.getBoundingClientRect() ?? fallbackRect;
  return source ? rectFromRect(source) : null;
}



export function useLinkFormState(): {
  formState: ILinkFormState;
  openLinkForm: (
    rect: DOMRect | null,
    mode: TLinkFormMode,
    buttonRef: React.RefObject<HTMLButtonElement | null>,
  ) => void;
  closeLinkForm: () => void;
  } {
  const [formState, setFormState] = useState<ILinkFormState>({
    isOpen: false,
    anchorRect: null,
    anchorElement: null,
    getAnchorRect: null,
    formMode: 'create-link-at-selection',
  });

  const openLinkForm = useCallback(
    (
      rect: DOMRect | null,
      mode: TLinkFormMode,
      buttonRef: React.RefObject<HTMLButtonElement | null>,
    ) => {
      const isSelectionMode = mode === 'create-link-at-selection';
      const windowScroll = { x: window.scrollX, y: window.scrollY };

      const { frozenRect, scrollSnapshots, anchorElement: selectionAnchor } = isSelectionMode
        ? captureSelectionAnchor(rect)
        : {
          frozenRect: captureButtonAnchor(buttonRef, rect),
          scrollSnapshots: [] as IScrollSnapshot[],
          anchorElement: null as HTMLElement | null,
        };

      const anchorElement = isSelectionMode
        ? selectionAnchor
        : buttonRef?.current ?? null;

      const getAnchorRect = (): DOMRect | null => {
        if (isSelectionMode) {
          if (!frozenRect) return null;
          return buildScrollAdjustedRect(frozenRect, windowScroll, scrollSnapshots);
        }
        const current = buttonRef?.current?.getBoundingClientRect();
        return current ? rectFromRect(current) : frozenRect;
      };

      setFormState({
        isOpen: true,
        anchorRect: frozenRect,
        anchorElement,
        getAnchorRect,
        formMode: mode,
      });
    },
    [],
  );

  const closeLinkForm = useCallback(() => {
    setFormState(prev => ({
      ...prev,
      isOpen: false,
      anchorRect: null,
      anchorElement: null,
      getAnchorRect: null,
    }));
  }, []);

  return {
    formState,
    openLinkForm,
    closeLinkForm,
  };
}

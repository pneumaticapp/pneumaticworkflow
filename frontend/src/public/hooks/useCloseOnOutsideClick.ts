import { RefObject, useEffect } from 'react';

const FLOATING_UI_SELECTOR = [
  '[data-tippy-root]',
  '.tippy-box',
  '.popover',
  '[role="listbox"]',
  '[role="menu"]',
  '[role="dialog"]',
].join(',');

export function useCloseOnOutsideClick(ref: RefObject<HTMLElement | null>, onClose: () => void): void {
  useEffect(() => {
    const handlePointerDown = (event: MouseEvent): void => {
      const { target } = event;
      if (!(target instanceof Node)) return;
      if (ref.current?.contains(target)) return;
      if (target instanceof Element && target.closest(FLOATING_UI_SELECTOR)) return;

      onClose();
    };

    document.addEventListener('mousedown', handlePointerDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
    };
  }, [ref, onClose]);
}

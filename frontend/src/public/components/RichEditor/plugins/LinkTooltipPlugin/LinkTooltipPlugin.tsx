import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

import { CustomTooltip } from '../../../UI';
import { truncateString } from '../../../../utils/truncateString';
import type { IHoveredLink } from './types';



const LINK_SELECTOR = 'a.lexical-rich-editor-link';
const TOOLTIP_MAX_URL_LENGTH = 50;

function getLinkFromTarget(target: EventTarget | null): HTMLAnchorElement | null {
  if (!target || (target as Node).nodeType !== Node.ELEMENT_NODE) return null;
  return (target as HTMLElement).closest(LINK_SELECTOR) as HTMLAnchorElement | null;
}

function getHref(anchor: HTMLAnchorElement): string {
  return anchor.getAttribute('href') ?? anchor.href ?? '';
}


export function LinkTooltipPlugin(): React.ReactElement | null {
  const [editor] = useLexicalComposerContext();
  const [hoveredLink, setHoveredLink] = useState<IHoveredLink | null>(null);
  const [refReady, setRefReady] = useState(false);
  const linkRef = useRef<HTMLAnchorElement | null>(null);

  useLayoutEffect(() => {
    if (hoveredLink) {
      linkRef.current = hoveredLink.element;
      setRefReady(true);
    } else {
      linkRef.current = null;
      setRefReady(false);
    }
  }, [hoveredLink]);

  useEffect(() => {
    const root = editor.getRootElement();
    if (!root) return () => {};

    const handleMouseOver = (e: MouseEvent): void => {
      const anchor = getLinkFromTarget(e.target);
      if (!anchor) return;
      const href = getHref(anchor);
      if (href) setHoveredLink({ element: anchor, href });
    };

    const handleMouseLeave = (e: MouseEvent): void => {
      setHoveredLink((prev) => {
        if (!prev) return null;
        const related = e.relatedTarget as Node | null;
        return !related || !prev.element.contains(related) ? null : prev;
      });
    };

    const unregisterUpdate = editor.registerUpdateListener(() => {
      setHoveredLink((prev) => (prev?.element.isConnected ? prev : null));
    });

    root.addEventListener('mouseover', handleMouseOver, true);
    root.addEventListener('mouseleave', handleMouseLeave, true);
    return () => {
      root.removeEventListener('mouseover', handleMouseOver, true);
      root.removeEventListener('mouseleave', handleMouseLeave, true);
      unregisterUpdate();
    };
  }, [editor]);

  const canShowTooltip =
    refReady &&
    hoveredLink &&
    typeof document !== 'undefined' &&
    Boolean(document.body);

  if (!canShowTooltip) return null;

  return createPortal(
    <CustomTooltip
      target={linkRef as React.RefObject<HTMLElement>}
      tooltipText={truncateString(hoveredLink.href, TOOLTIP_MAX_URL_LENGTH)}
      isOpen
      isModal={false}
    />,
    document.body,
  );
}

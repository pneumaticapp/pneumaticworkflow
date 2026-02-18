import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

import { CustomTooltip } from '../../../UI';



// Constants
const VARIABLE_CHIP_SELECTOR = '.lexical-rich-editor-variable';
const VARIABLE_TITLE_ATTRIBUTE = 'data-lexical-variable-title';
const VARIABLE_SUBTITLE_ATTRIBUTE = 'data-lexical-variable-subtitle';

/**
 * Represents a hovered variable element with its data.
 */
interface IHoveredVariable {
  /** The DOM element of the hovered variable */
  element: HTMLElement;
  /** The title text of the variable */
  title: string;
  /** The subtitle text of the variable */
  subtitle: string;
}

/**
 * Extracts variable element from mouse event target.
 * @param event - The mouse event
 * @returns Variable HTMLElement or null if not found
 */
function getVariableElementFromEvent(event: MouseEvent): HTMLElement | null {
  if ((event.target as Node).nodeType !== Node.ELEMENT_NODE) {
    return null;
  }
  return (event.target as HTMLElement).closest?.(VARIABLE_CHIP_SELECTOR) as HTMLElement | null;
}

/**
 * Extracts title and subtitle data from variable element.
 * @param element - The variable DOM element
 * @returns Object with element, title, and subtitle
 */
function extractVariableData(element: HTMLElement): IHoveredVariable {
  const title = element.getAttribute(VARIABLE_TITLE_ATTRIBUTE) ?? '';
  const subtitle = element.getAttribute(VARIABLE_SUBTITLE_ATTRIBUTE) ?? '';

  return {
    element,
    title,
    subtitle,
  };
}


/**
 * Plugin that shows tooltips when hovering over variable chips in the rich text editor.
 * Displays variable title and subtitle similar to the old editor (Badge + CustomTooltip).
 *
 * @returns React element for the tooltip portal or null if no tooltip should be shown
 */
export function VariableTooltipPlugin(): React.ReactElement | null {
  const [editor] = useLexicalComposerContext();
  const [hoveredVariable, setHoveredVariable] = useState<IHoveredVariable | null>(null);
  const [refReady, setRefReady] = useState(false);
  const targetRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    if (hoveredVariable) {
      targetRef.current = hoveredVariable.element;
      setRefReady(true);
    } else {
      targetRef.current = null;
      setRefReady(false);
    }
  }, [hoveredVariable]);

  /**
   * Handles mouseover events on variable elements.
   * Finds the closest variable chip and extracts its data for tooltip display.
   */
  const handleMouseOver = useCallback((event: MouseEvent): void => {
    const target = getVariableElementFromEvent(event);
    if (target) {
      const variableData = extractVariableData(target);
      setHoveredVariable(variableData);
    }
  }, []);

  /**
   * Handles mouseleave events.
   * Hides tooltip when mouse leaves the variable element (not moving to child elements).
   */
  const handleMouseLeave = useCallback((event: MouseEvent): void => {
    setHoveredVariable((prev) => {
      if (!prev) return null;
      const relatedTarget = event.relatedTarget as Node | null;
      const hasLeftChip = !relatedTarget || !prev.element.contains(relatedTarget);
      return hasLeftChip ? null : prev;
    });
  }, []);

  /**
   * Sets up mouse event listeners for variable tooltips.
   * Handles mouseover to show tooltip and mouseleave to hide it.
   */
  useEffect(() => {
    const root = editor.getRootElement();
    if (!root) return () => {};

    root.addEventListener('mouseover', handleMouseOver, true);
    root.addEventListener('mouseleave', handleMouseLeave, true);

    return () => {
      root.removeEventListener('mouseover', handleMouseOver, true);
      root.removeEventListener('mouseleave', handleMouseLeave, true);
    };
  }, [editor, handleMouseOver, handleMouseLeave]);

  /**
   * Listens for editor updates to clean up stale tooltip references.
   * Removes tooltip if the variable element is no longer connected to the DOM.
   */
  useEffect(() => {
    return editor.registerUpdateListener(() => {
      setHoveredVariable((prev) => {
        if (!prev) return null;
        if (!prev.element.isConnected) return null;
        return prev;
      });
    });
  }, [editor]);

  if (
    !refReady ||
    !hoveredVariable ||
    typeof document === 'undefined' ||
    !document.body
  ) {
    return null;
  }

  return createPortal(
    <CustomTooltip
      target={targetRef as React.RefObject<HTMLElement>}
      tooltipText={hoveredVariable.subtitle}
      isOpen
      isModal={false}
    />,
    document.body,
  );
}

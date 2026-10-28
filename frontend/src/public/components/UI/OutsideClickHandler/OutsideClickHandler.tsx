import * as React from 'react';
import { useRef, useEffect } from 'react';
import { IOutsideClickHandlerProperties } from './types';

export const OutsideClickHandler = ({
  children,
  onOutsideClick,
  disabled = false,
  useCapture = true,
  display = 'block',
}: IOutsideClickHandlerProperties) => {
  const wrapperReference = useRef<HTMLDivElement>(null);
  const onOutsideClickReference = useRef(onOutsideClick);
  onOutsideClickReference.current = onOutsideClick;

  useEffect(() => {
    if (disabled) {
      return undefined;
    }

    let removeMouseUpListener: (() => void) | null = null;

    const handleMouseUp = (event: MouseEvent) => {
      if (removeMouseUpListener) {
        removeMouseUpListener();
        removeMouseUpListener = null;
      }

      const wrapperElement = wrapperReference.current;
      const isDescendant = wrapperElement && event.target instanceof Node && wrapperElement.contains(event.target);

      if (!isDescendant) {
        onOutsideClickReference.current(event);
      }
    };

    const handleMouseDown = (event: MouseEvent) => {
      const wrapperElement = wrapperReference.current;
      const isDescendant = wrapperElement && event.target instanceof Node && wrapperElement.contains(event.target);

      if (!isDescendant) {
        if (removeMouseUpListener) {
          removeMouseUpListener();
          removeMouseUpListener = null;
        }

        document.addEventListener('mouseup', handleMouseUp, { capture: useCapture });
        removeMouseUpListener = () => {
          document.removeEventListener('mouseup', handleMouseUp, { capture: useCapture });
        };
      }
    };

    document.addEventListener('mousedown', handleMouseDown, { capture: useCapture });

    return () => {
      document.removeEventListener('mousedown', handleMouseDown, { capture: useCapture });
      if (removeMouseUpListener) {
        removeMouseUpListener();
      }
    };
  }, [disabled, useCapture]);

  const style = display !== 'block' ? { display } : undefined;

  return (
    <div ref={wrapperReference} style={style}>
      {children}
    </div>
  );
};

export default OutsideClickHandler;

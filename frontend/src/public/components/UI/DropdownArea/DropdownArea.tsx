import * as React from 'react';
import classnames from 'classnames';
import { usePopper } from 'react-popper';
import OutsideClickHandler from 'react-outside-click-handler';

import { useDidUpdateEffect } from '../../../hooks/useDidUpdateEffect';
import { DropdownControl } from '../DropdownControl';
import { DropdownAreaHandle, IDropdownAreaProps } from './types';

import styles from './DropdownArea.css';

export const DropdownArea = React.forwardRef<DropdownAreaHandle, IDropdownAreaProps>((
  {
    children,
    toggle,
    title,
    containerClassName,
    placement = 'bottom-start',
    onOpen,
    onClose,
  },
  ref,
) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [referenceElement, setReferenceElement] = React.useState<HTMLButtonElement | null>(null);
  const [popperElement, setPopperElement] = React.useState<HTMLDivElement | null>(null);

  const {
    styles: popperStyles,
    attributes,
    update: updateDropdownPosition,
  } = usePopper(referenceElement, popperElement, { placement });

  React.useImperativeHandle(ref, () => ({
    updateDropdownPosition: updateDropdownPosition || (() => undefined),
    closeDropdown: () => setIsOpen(false),
  }));

  useDidUpdateEffect(() => {
    const handleUpdates = async () => {
      await updateDropdownPosition?.();
      const callback = isOpen ? onOpen : onClose;
      callback?.();
    };

    handleUpdates();
  }, [isOpen]);

  const handleOutsideClick = React.useCallback(() => {
    if (isOpen) {
      setIsOpen(false);
    }
  }, [isOpen]);

  return (
    <OutsideClickHandler onOutsideClick={handleOutsideClick}>
      <div className={classnames(styles['container'], isOpen && styles['container_is-open'], containerClassName)}>
        <button
          type="button"
          aria-expanded={isOpen}
          className={styles['toggle']}
          onClick={() => setIsOpen(!isOpen)}
          ref={setReferenceElement}
        >
          {toggle || <DropdownControl title={title} isOpen={isOpen} />}
        </button>
        <div
          className={styles['content']}
          ref={setPopperElement}
          style={popperStyles.popper}
          {...attributes.popper}
        >
          {children}
        </div>
      </div>
    </OutsideClickHandler>
  );
});

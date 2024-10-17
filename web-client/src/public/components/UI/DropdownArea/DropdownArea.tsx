/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { usePopper } from 'react-popper';
import { Placement } from 'popper.js';
import OutsideClickHandler from 'react-outside-click-handler';

import { useDidUpdateEffect } from '../../../hooks/useDidUpdateEffect';
import { ExpandIcon } from '../../icons';

import styles from './DropdownArea.css';

export interface IDropdownAreaProps {
  children: React.ReactNode;
  title?: string;
  containerClassName?: string;
  toggle?: React.ReactNode;
  placement?: Placement;
  onOpen?(): void;
  onClose?(): void;
}

export type DropdownAreaHandle = {
  updateDropdownPosition(): void;
  closeDropdown(): void;
};

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
  const { useState, useImperativeHandle } = React;
  const [isOpen, setIsOpen] = useState(false);
  const [referenceElement, setReferenceElement] = useState<HTMLButtonElement | null>(null);
  const [popperElement, setPopperElement] = useState<HTMLDivElement | null>(null);

  const {
    styles: popperStyles,
    attributes,
    update: updateDropdownPosition,
  } = usePopper(referenceElement, popperElement, { placement });

  useImperativeHandle(ref, () => ({
    updateDropdownPosition: updateDropdownPosition || (() => { }),
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

  const onOutsideClick = React.useCallback(() => {
    if (isOpen) {
      setIsOpen(false);
    }
  }, [isOpen, setIsOpen]);


  const renderToggle = () => {
    if (toggle) {
      return toggle;
    }

    return (
      <p className={styles['control']}>
        <span className={styles['control-value']}>{title}</span>
        <ExpandIcon className={styles['control-arrow']} />
      </p>
    )
  }

  return (
    <OutsideClickHandler onOutsideClick={onOutsideClick}>
      <div className={classnames(styles['container'], isOpen && styles['container_is-open'], containerClassName)}>
        <button
          className={styles['toggle']}
          onClick={() => setIsOpen(!isOpen)}
          ref={setReferenceElement}
        >
          {renderToggle()}
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

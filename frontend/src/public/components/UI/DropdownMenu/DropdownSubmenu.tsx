import React, { useLayoutEffect, useRef, useState } from 'react';
import classnames from 'classnames';
import OutsideClickHandler from 'react-outside-click-handler';

import { ArrowRightIcon } from '../../icons';
import type { IDropdownSubmenuProps } from './types';

import styles from './DropdownMenu.css';

export function DropdownSubmenu({ label, className, toggleClassName, renderPanel }: IDropdownSubmenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isOpenToLeft, setIsOpenToLeft] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!isOpen) {
      setIsOpenToLeft(false);
      return;
    }

    const panel = containerRef.current?.querySelector<HTMLElement>(':scope > [role="menu"]');
    if (panel && panel.getBoundingClientRect().right > document.documentElement.clientWidth) {
      setIsOpenToLeft(true);
    }
  }, [isOpen]);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const handleOutsideClick = () => {
    setIsOpen(false);
  };

  return (
    <OutsideClickHandler disabled={!isOpen} onOutsideClick={handleOutsideClick}>
      <div
        ref={containerRef}
        className={classnames(styles['submenu'], isOpenToLeft && styles['submenu_left'], className)}
      >
        <button
          type="button"
          role="menuitem"
          aria-haspopup="true"
          aria-expanded={isOpen}
          className={toggleClassName}
          onClick={handleToggle}
        >
          <span className={styles['label']}>{label}</span>
          <ArrowRightIcon className={styles['dropdown-item-icon']} />
        </button>
        {renderPanel(isOpen)}
      </div>
    </OutsideClickHandler>
  );
}

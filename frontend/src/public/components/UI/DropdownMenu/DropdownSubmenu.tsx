import React, { useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import classnames from 'classnames';
import OutsideClickHandler from 'react-outside-click-handler';

import { ArrowRightIcon } from '../../icons';
import { getSubmenuPlacement } from './utils/getSubmenuPlacement';
import type { IDropdownSubmenuProps, TSubmenuPlacement } from './types';

import styles from './DropdownMenu.css';

export function DropdownSubmenu({ label, className, toggleClassName, renderPanel }: IDropdownSubmenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [placement, setPlacement] = useState<TSubmenuPlacement>({ side: 'right' });
  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!isOpen) {
      setPlacement({ side: 'right' });
      return;
    }

    const container = containerRef.current;
    const panel = container?.querySelector<HTMLElement>(':scope > [role="menu"]');
    if (!container || !panel) return;

    const panelRect = panel.getBoundingClientRect();
    if (panelRect.right <= document.documentElement.clientWidth) return;

    setPlacement(
      getSubmenuPlacement(container.getBoundingClientRect(), panelRect.width, document.documentElement.clientWidth),
    );
  }, [isOpen]);

  const placementStyle =
    placement.side === 'shifted' ? ({ '--submenu-left': `${placement.left}px` } as CSSProperties) : undefined;

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
        className={classnames(
          styles['submenu'],
          placement.side === 'left' && styles['submenu_left'],
          placement.side === 'shifted' && styles['submenu_shifted'],
          className,
        )}
        style={placementStyle}
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

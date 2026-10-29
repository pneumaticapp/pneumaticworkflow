import * as React from 'react';
import classnames from 'classnames';

import type { IDropdownMenuPanelProps } from './types';

import styles from './DropdownMenu.css';

export function DropdownMenuPanel({
  renderedOptions,
  isOpen,
  isWide,
  level,
  direction = 'right',
  className,
  renderMenuContent,
}: IDropdownMenuPanelProps) {
  const content = renderMenuContent?.(renderedOptions) || renderedOptions;

  return (
    <div
      role="menu"
      tabIndex={-1}
      aria-hidden={!isOpen}
      className={classnames(
        styles['dropdown-menu'],
        isWide && styles['dropdown-menu_wide'],
        level === 0 && direction === 'right' && styles['dropdown-menu_right'],
        level > 0 && styles['dropdown-menu_submenu'],
        isOpen && styles['dropdown-menu_show'],
        className,
      )}
    >
      {content}
    </div>
  );
}

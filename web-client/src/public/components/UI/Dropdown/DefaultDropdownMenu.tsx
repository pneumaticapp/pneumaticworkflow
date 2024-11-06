import React from 'react';
import { DropdownMenu } from 'reactstrap';
import classnames from 'classnames';
import { IDropdownMenuProps } from '../../../types/workflow';
import styles from './Dropdown.css';

export function DefaultDropdownMenu({
  renderedOptions,
  isWide,
  level,
  direction = 'right',
  className,
  renderMenuContent,
}: IDropdownMenuProps) {
  const content = renderMenuContent?.(renderedOptions) || renderedOptions;

  return (
    <DropdownMenu
      cssModule={{
        'dropdown-menu': classnames(styles['dropdown-menu'], isWide && styles['dropdown-menu_wide']),
        show: styles['dropdown-menu_show'],
      }}
      right={level === 0 && direction === 'right'}
      className={className}
      modifiers={{ preventOverflow: { boundariesElement: 'window' } }}
    >
      {content}
    </DropdownMenu>
  );
}

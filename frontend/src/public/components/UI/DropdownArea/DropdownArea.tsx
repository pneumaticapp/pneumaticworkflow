import React from 'react';

import { Dropdown } from '../Dropdown';
import { DropdownControl } from '../DropdownControl';
import { DropdownAreaHandle, IDropdownAreaProps } from './types';

import styles from './DropdownArea.css';

export const DropdownArea = React.forwardRef<DropdownAreaHandle, IDropdownAreaProps>(({
  children,
  toggle,
  title,
  containerClassName,
  placement = 'bottom-start',
  onOpen,
  onClose,
}, ref) => (
  <Dropdown
    dropdownRef={ref}
    placement={placement}
    className={containerClassName}
    menuClassName={styles['content']}
    renderToggle={(isOpen) => toggle || <DropdownControl title={title} isOpen={isOpen} />}
    onOpen={onOpen}
    onClose={onClose}
  >
    {children}
  </Dropdown>
));

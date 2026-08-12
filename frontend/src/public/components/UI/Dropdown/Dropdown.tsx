import React, { useCallback, useEffect, useImperativeHandle, useState } from 'react';
import { createPortal } from 'react-dom';
import classnames from 'classnames';
import { usePopper } from 'react-popper';

import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { useDidUpdateEffect } from '../../../hooks/useDidUpdateEffect';
import { DropdownSurface } from '../DropdownSurface';
import { DropdownOptions } from './DropdownOptions';
import { IDropdownProps } from './types';

import styles from './Dropdown.css';

export type { IDropdownHandle, IDropdownProps, TDropdownOption } from './types';

export function Dropdown({
  options,
  children,
  direction,
  placement,
  className,
  toggleProps,
  menuClassName,
  menuPositionFixed = false,
  menuContainer,
  renderToggle,
  renderMenuContent,
  isFromBreakdownItem,
  isDisabled = false,
  onOpen,
  onClose,
  dropdownRef,
}: IDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [referenceElement, setReferenceElement] = useState<HTMLButtonElement | null>(null);
  const [menuElement, setMenuElement] = useState<HTMLDivElement | null>(null);
  const { isDesktop } = useCheckDevice();
  const resolvedPlacement = placement || (direction === 'right' ? 'bottom-end' : 'bottom-start');
  const { styles: popperStyles, attributes, update } = usePopper(referenceElement, menuElement, {
    placement: resolvedPlacement,
    strategy: menuPositionFixed ? 'fixed' : 'absolute',
    modifiers: [{ name: 'preventOverflow', options: { rootBoundary: 'viewport' } }],
  });

  const closeDropdown = useCallback(() => setIsOpen(false), []);
  const toggleDropdown = () => {
    if (!isDisabled) setIsOpen((current) => !current);
  };

  useImperativeHandle(dropdownRef, () => ({
    updateDropdownPosition: () => { update?.(); },
    closeDropdown,
  }));

  useDidUpdateEffect(() => {
    update?.();
    (isOpen ? onOpen : onClose)?.();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return undefined;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!referenceElement?.contains(target) && !menuElement?.contains(target)) closeDropdown();
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      closeDropdown();
      referenceElement?.focus();
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [closeDropdown, isOpen, menuElement, referenceElement]);

  const renderedContent = typeof children === 'function'
    ? children({ closeDropdown })
    : children || (options && (
      <DropdownOptions
        options={options}
        closeDropdown={closeDropdown}
        isFromBreakdownItem={isFromBreakdownItem}
      />
    ));
  const menuContent = renderMenuContent?.(renderedContent) || renderedContent;
  const isWide = options && !Array.isArray(options)
    ? Boolean(options.customSubOption)
    : Boolean(options?.length && options.every((option) => option.size === 'lg'));
  const hasSubmenu = Boolean(Array.isArray(options) && options.some((option) => (
    option.customSubOption || (Array.isArray(option.subOptions) && option.subOptions.length)
  )));
  const menu = isOpen && menuContent ? (
    <DropdownSurface
      ref={setMenuElement}
      role="menu"
      tabIndex={-1}
      className={classnames(
        styles['dropdown-menu'],
        isWide && styles['dropdown-menu_wide'],
        hasSubmenu && styles['dropdown-menu_with-submenu'],
        menuClassName,
      )}
      style={popperStyles.popper}
      {...attributes.popper}
    >
      {menuContent}
    </DropdownSurface>
  ) : null;
  let portalTarget: Element | null | undefined;
  if (typeof document !== 'undefined') {
    portalTarget = typeof menuContainer === 'string' ? document.querySelector(menuContainer) : menuContainer;
  }

  const { className: toggleClassName, ...buttonProps } = toggleProps || {};

  return (
    <div
      className={classnames(
        styles['container'],
        isFromBreakdownItem && isDesktop && styles['dropdown-toggle-centered-container'],
        className,
      )}
    >
      <button
        type="button"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        className={classnames(
          styles['dropdown-toggle'],
          isFromBreakdownItem && isDesktop && styles['dropdown-toggle-centered'],
          toggleClassName,
        )}
        disabled={isDisabled}
        onClick={(event) => {
          event.stopPropagation();
          toggleDropdown();
        }}
        ref={setReferenceElement}
        {...buttonProps}
      >
        {renderToggle(isOpen)}
      </button>
      {portalTarget && menu ? createPortal(menu, portalTarget) : menu}
    </div>
  );
}

import React, { useRef, useState } from 'react';
import classnames from 'classnames';
import OutsideClickHandler from 'react-outside-click-handler';

import { DropdownMenuItem } from './DropdownMenuItem';
import { DropdownMenuPanel } from './DropdownMenuPanel';
import { DropdownSubmenu } from './DropdownSubmenu';
import { getDropdownItemColorClass } from './utils/getDropdownItemColorClass';
import { isTextEntryTarget } from './utils/isTextEntryTarget';
import { moveMenuItemFocus } from './utils/moveMenuItemFocus';
import type { IDropdownMenuProps, TDropdownMenuOption } from './types';
import { isArrayWithItems } from '../../../utils/helpers';
import { useCheckDevice } from '../../../hooks/useCheckDevice';

import styles from './DropdownMenu.css';

const getOptionKey = ({ label, mapKey }: TDropdownMenuOption) => (typeof label === 'string' ? label : mapKey);

export function DropdownMenu({
  options,
  direction,
  className,
  toggleProps,
  menuClassName,
  renderToggle,
  renderMenuContent,
  isFromBreakdownItem,
  isDisabled = false,
}: IDropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const { isDesktop, isMobile } = useCheckDevice();

  const handleToggle = () => {
    if (isDisabled) return;
    setIsOpen((prev) => !prev);
  };

  const closeDropdown = () => {
    setIsOpen(false);
  };

  const handleContainerClick = (event: React.MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
  };

  const handleContainerKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!isOpen || event.defaultPrevented || isTextEntryTarget(event.target)) return;

    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      closeDropdown();
      toggleRef.current?.focus();
      return;
    }

    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      moveMenuItemFocus(event.currentTarget, event.key === 'ArrowDown' ? 1 : -1);
    }
  };

  const renderOption = (option: TDropdownMenuOption, level: number) => {
    const { label, customSubOption, color, subOptions, isHidden, disabledTooltip } = option;
    const { isDisabled: isOptionDisabled, className: optionClassName } = option;
    if (isHidden) return null;

    if (customSubOption || (Array.isArray(subOptions) && isArrayWithItems(subOptions))) {
      const renderSubmenuPanel = (isSubmenuOpen: boolean) =>
        subOptions ? (
          renderOptions(subOptions, level + 1, isSubmenuOpen)
        ) : (
          <DropdownMenuPanel
            className={styles['dropdown__custom-sub-options']}
            renderedOptions={customSubOption}
            isOpen={isSubmenuOpen}
            isWide
            level={level + 1}
          />
        );

      return (
        <DropdownSubmenu
          key={`submenu-${getOptionKey(option)}`}
          label={label}
          className={optionClassName}
          toggleClassName={classnames(styles['dropdown-item'], getDropdownItemColorClass(color))}
          renderPanel={renderSubmenuPanel}
        />
      );
    }

    const key = `${isOptionDisabled && disabledTooltip ? 'disabled' : 'option'}-${getOptionKey(option)}`;

    return (
      <DropdownMenuItem
        key={key}
        option={option}
        isSpaced={Boolean(isMobile && isFromBreakdownItem)}
        closeDropdown={closeDropdown}
      />
    );
  };

  function renderOptions(items: TDropdownMenuOption[] | TDropdownMenuOption, level: number, isMenuOpen: boolean) {
    const isRootLevel = level === 0;
    const isWide = !Array.isArray(items) || items.every((item) => item.size === 'lg');
    const renderedOptions = Array.isArray(items)
      ? items.map((item) => renderOption(item, level))
      : items.customSubOption;

    return (
      <DropdownMenuPanel
        renderedOptions={renderedOptions}
        isOpen={isMenuOpen}
        isWide={isWide}
        level={level}
        direction={direction}
        className={menuClassName}
        {...((isRootLevel || !Array.isArray(items)) && { renderMenuContent })}
      />
    );
  }

  return (
    <OutsideClickHandler disabled={!isOpen} onOutsideClick={closeDropdown}>
      <div
        role="presentation"
        className={classnames(
          styles['container'],
          isFromBreakdownItem && isDesktop && styles['dropdown-toggle-centered-container'],
          className,
        )}
        onClick={handleContainerClick}
        onKeyDown={handleContainerKeyDown}
      >
        <button
          ref={toggleRef}
          type="button"
          aria-haspopup="true"
          aria-expanded={isOpen}
          className={classnames(
            styles['dropdown-toggle'],
            isFromBreakdownItem && isDesktop && styles['dropdown-toggle-centered'],
          )}
          disabled={isDisabled}
          {...toggleProps}
          onClick={handleToggle}
        >
          {renderToggle(isOpen)}
        </button>
        {renderOptions(options, 0, isOpen)}
      </div>
    </OutsideClickHandler>
  );
}

import React, { ChangeEvent } from 'react';
import classnames from 'classnames';
import PerfectScrollbar from 'react-perfect-scrollbar';
import { components } from 'react-select';

import { ArrowDropdownIcon } from '../../icons';
import { DropdownControl } from '../DropdownControl';
import { DropdownSurface } from '../DropdownSurface';
import { InputField } from '../Fields/InputField';
import { DropdownOption } from './DropdownOption';
import { IDropdownListSelectComponentsProps, TDropdownOptionBase } from './types';

import styles from './DropdownList.css';

const ScrollBar = PerfectScrollbar as unknown as Function;
const renderNothing = () => null;

/**
 * react-select remounts every custom component whose identity changes between renders, which
 * detaches the option nodes mid-interaction. So the components are built once per DropdownList
 * instance and read the current render's data through `getProps`.
 */
export function createDropdownListComponents<TOption extends TDropdownOptionBase>(
  getProps: () => IDropdownListSelectComponentsProps<TOption>,
) {
  const SelectControl = (props: any) => {
    const {
      controlSize, title, label, placeholder, selectedLabel, isDisabled, staticMenu, isMenuOpen,
      onToggleMenu, errorMessage, controlClassName,
    } = getProps();
    const { menuIsOpen } = props;
    if (staticMenu) return null;

    return (
      <components.Control {...props}>
        <button
          type="button"
          className={styles['dropdown-list__toggle']}
          aria-label={title || label}
          aria-haspopup="listbox"
          aria-expanded={isMenuOpen}
          disabled={isDisabled}
          onMouseDown={(event) => event.stopPropagation()}
          onClick={onToggleMenu}
        >
          {controlSize === 'sm' ? (
            <DropdownControl
              title={title || selectedLabel || placeholder}
              isOpen={menuIsOpen}
              className={controlClassName}
            />
          ) : (
            <span
              className={classnames(
                styles['dropdown-list__control'],
                menuIsOpen && styles['dropdown-list__control_open'],
                errorMessage && styles['dropdown-list__control_error'],
                controlClassName,
              )}
            >
              <span
                className={classnames(
                  styles['dropdown-list__value'],
                  !selectedLabel && styles['dropdown-list__value_placeholder'],
                )}
              >
                {selectedLabel || placeholder}
              </span>
              <ArrowDropdownIcon
                className={classnames(
                  styles['dropdown-list__arrow'],
                  menuIsOpen && styles['dropdown-list__arrow_open'],
                )}
              />
            </span>
          )}
        </button>
      </components.Control>
    );
  };

  const SelectMenu = ({ children, ...props }: any) => {
    const { controlSize, isMulti, staticMenu, placement, menuClassName } = getProps();

    return (
      <components.Menu {...props}>
        <DropdownSurface
          role="listbox"
          aria-multiselectable={isMulti || undefined}
          className={classnames(
            styles[`dropdown-list__menu_${controlSize}`],
            placement === 'left' && styles['dropdown-list__menu_left'],
            staticMenu && styles['dropdown-list__menu_static'],
            menuClassName,
          )}
        >
          {children}
        </DropdownSurface>
      </components.Menu>
    );
  };

  const SelectMenuList = ({ children }: any) => {
    const { isSearchable, searchText, placeholder, onSearchChange } = getProps();

    return (
      <>
        {isSearchable && (
          <>
            <div className={styles['dropdown-list__search']}>
              <InputField
                value={searchText}
                onChange={(event: ChangeEvent<HTMLInputElement>) => onSearchChange(event.target.value)}
                onClear={() => onSearchChange('')}
                className={styles['dropdown-list__search-input']}
                fieldSize="md"
                autoFocus
                autoComplete="one-time-code"
                name="dropdown-list-search"
                placeholder={typeof placeholder === 'string' ? placeholder : undefined}
              />
            </div>
            <hr className={styles['dropdown-list__search-separator']} />
          </>
        )}
        <ScrollBar
          className={styles['dropdown-list__scrollbar']}
          options={{ suppressScrollX: true, wheelPropagation: false }}
        >
          {children}
        </ScrollBar>
      </>
    );
  };

  const SelectOption = ({ data, innerProps, innerRef, isSelected, isFocused }: any) => {
    const { selectValue, searchText, isDisabled, getOptionLabel, formatOptionLabel } = getProps();
    const { label: optionLabel } = data;
    const { onClick: onOptionClick, ...optionProps } = innerProps;
    const content = formatOptionLabel
      ? formatOptionLabel(data, { context: 'menu', selectValue, inputValue: searchText })
      : <DropdownOption label={getOptionLabel ? getOptionLabel(data) : optionLabel} isSelected={isSelected} />;

    return (
      <button
        {...optionProps}
        type="button"
        role="option"
        aria-selected={isSelected}
        ref={innerRef}
        disabled={isDisabled}
        className={classnames(
          styles['dropdown-list__option'],
          isFocused && styles['dropdown-list__option_focused'],
        )}
        onClick={isDisabled ? undefined : onOptionClick}
      >
        {content}
      </button>
    );
  };

  const SelectGroupHeading = ({ children }: any) => (
    <div className={styles['dropdown-list__group-heading']}>{children}</div>
  );

  const SelectNoOptionsMessage = () => (
    <div className={styles['dropdown-list__no-options']}>{getProps().noOptionsMessage}</div>
  );

  return {
    Control: SelectControl,
    Menu: SelectMenu,
    MenuList: SelectMenuList,
    Option: SelectOption,
    GroupHeading: SelectGroupHeading,
    NoOptionsMessage: SelectNoOptionsMessage,
    IndicatorSeparator: renderNothing,
    DropdownIndicator: renderNothing,
  };
}

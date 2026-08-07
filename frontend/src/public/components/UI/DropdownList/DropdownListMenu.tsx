import React, { ChangeEvent, ReactNode } from 'react';
import PerfectScrollbar from 'react-perfect-scrollbar';

import { InputField } from '../Fields/InputField';
import { DropdownOption } from './DropdownOption';
import { IDropdownListMenuProps, TDropdownOptionBase, TDropdownOptionGroup } from './types';
import { isOptionGroup } from './utils';

import styles from './DropdownList.css';

const ScrollBar = PerfectScrollbar as unknown as Function;

export function DropdownListMenu<TOption extends TDropdownOptionBase>({
  options,
  isSearchable,
  isDisabled,
  placeholder,
  noOptionsMessage,
  selectValue,
  searchText,
  getOptionLabel,
  formatOptionLabel,
  onSearchChange,
  onSelect,
  isSelected,
}: IDropdownListMenuProps<TOption>) {
  const renderOption = (option: TOption, key: string) => {
    const selected = isSelected(option);
    const content: ReactNode = formatOptionLabel
      ? formatOptionLabel(option, { context: 'menu', selectValue, inputValue: searchText })
      : <DropdownOption label={getOptionLabel ? getOptionLabel(option) : option.label} isSelected={selected} />;

    return (
      <button
        type="button"
        role="option"
        aria-selected={selected}
        key={key}
        disabled={isDisabled}
        className={styles['dropdown-list__option']}
        onClick={() => onSelect(option)}
      >
        {content}
      </button>
    );
  };

  const renderGroup = (group: TDropdownOptionGroup<TOption>, groupKey: string) => (
    <div className={styles['dropdown-list__group']} key={groupKey}>
      <div className={styles['dropdown-list__group-heading']}>{group.label}</div>
      {group.options.map((option, index) => renderOption(option, `${groupKey}-${index}`))}
    </div>
  );

  const hasOptions = options.some((item) => (isOptionGroup(item) ? item.options.length > 0 : true));

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
        {hasOptions ? (
          options.map((item, index) => (
            isOptionGroup(item)
              ? renderGroup(item, `group-${index}`)
              : renderOption(item, `option-${index}`)
          ))
        ) : (
          <div className={styles['dropdown-list__no-options']}>{noOptionsMessage}</div>
        )}
      </ScrollBar>
    </>
  );
}

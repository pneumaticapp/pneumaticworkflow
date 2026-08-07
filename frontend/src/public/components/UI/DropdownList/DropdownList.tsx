import React, { ReactNode, useMemo, useState } from 'react';
import classnames from 'classnames';
import { FieldHookConfig, useField } from 'formik';

import { ArrowDropdownIcon } from '../../icons';
import { Dropdown } from '../Dropdown';
import { DropdownControl } from '../DropdownControl';
import { DropdownSurface } from '../DropdownSurface';
import { DropdownListMenu } from './DropdownListMenu';
import { IDropdownListProps, TDropdownOptionBase } from './types';
import { flattenOptions, getDefaultOptionValue, getOptionSearchText, isOptionGroup, toArray } from './utils';

import styles from './DropdownList.css';

export function DropdownList<TOption extends TDropdownOptionBase>({
  options,
  value,
  defaultValue,
  onChange,
  isMulti = false,
  isSearchable = false,
  isDisabled = false,
  isRequired = false,
  label,
  title,
  placeholder,
  controlSize = 'lg',
  className,
  controlClassName,
  menuClassName,
  placement,
  staticMenu = false,
  closeMenuOnSelect,
  errorMessage,
  noOptionsMessage = 'No options',
  getOptionLabel,
  getOptionValue,
  formatOptionLabel,
  filterOption,
  onInputChange,
}: IDropdownListProps<TOption>) {
  const [searchText, setSearchText] = useState('');
  const [uncontrolledValue, setUncontrolledValue] = useState<TOption | TOption[] | null>(defaultValue ?? null);
  const isControlled = value !== undefined;
  const selectValue = toArray(isControlled ? value : uncontrolledValue);
  const shouldCloseOnSelect = closeMenuOnSelect ?? !isMulti;

  const optionKey = (option: TOption) => (getOptionValue ? getOptionValue(option) : getDefaultOptionValue(option));
  const isSameOption = (a: TOption, b: TOption) => {
    const keyA = optionKey(a);
    const keyB = optionKey(b);
    if (keyA !== undefined && keyB !== undefined) return keyA === keyB;
    return a === b;
  };
  const isSelected = (option: TOption) => selectValue.some((selected) => isSameOption(selected, option));

  const filteredOptions = useMemo(() => {
    const matches = (option: TOption) => {
      if (!searchText) return true;
      const optionLabel = getOptionSearchText(option, getOptionLabel);
      if (filterOption) {
        return filterOption({ label: optionLabel, value: optionKey(option) || '', data: option }, searchText);
      }

      return optionLabel.toLowerCase().includes(searchText.toLowerCase());
    };

    return options
      .map((item) => (isOptionGroup(item) ? { ...item, options: item.options.filter(matches) } : item))
      .filter((item) => (isOptionGroup(item) ? item.options.length > 0 : matches(item)));
  }, [options, searchText, filterOption, getOptionLabel, getOptionValue]);

  const handleSearchChange = (nextSearch: string) => {
    setSearchText(nextSearch);
    onInputChange?.(nextSearch);
  };

  const handleSelect = (option: TOption, closeDropdown: () => void) => {
    // Options may carry their own action (invite a teammate, select all) instead of being selectable.
    if (option.onClick) {
      option.onClick();
      return;
    }

    const wasSelected = isSelected(option);
    const getNextValue = () => {
      if (!isMulti) return option;
      return wasSelected ? selectValue.filter((item) => !isSameOption(item, option)) : [...selectValue, option];
    };
    const nextValue = getNextValue();

    if (!isControlled) setUncontrolledValue(nextValue);
    onChange?.(nextValue, { action: wasSelected ? 'deselect-option' : 'select-option', option });

    if (searchText) handleSearchChange('');
    if (shouldCloseOnSelect) closeDropdown();
  };

  const renderMenu = (closeDropdown: () => void) => (
    <DropdownListMenu<TOption>
      options={filteredOptions}
      isMulti={isMulti}
      isSearchable={isSearchable}
      isDisabled={isDisabled}
      placeholder={placeholder}
      noOptionsMessage={noOptionsMessage}
      selectValue={selectValue}
      searchText={searchText}
      getOptionLabel={getOptionLabel}
      formatOptionLabel={formatOptionLabel}
      onSearchChange={handleSearchChange}
      onSelect={(option) => handleSelect(option, closeDropdown)}
      isSelected={isSelected}
    />
  );

  const labelNode = label ? (
    <p className={styles['dropdown-list__label']}>
      {label}
      {isRequired && <span className={styles['dropdown-list__required']}>*</span>}
    </p>
  ) : null;
  const errorNode = errorMessage ? <p className={styles['dropdown-list__error']}>{errorMessage}</p> : null;

  if (staticMenu) {
    return (
      <div className={classnames(styles['dropdown-list'], isDisabled && styles['dropdown-list_disabled'], className)}>
        {labelNode}
        <DropdownSurface className={classnames(styles['dropdown-list__menu_static'], menuClassName)}>
          {renderMenu(() => undefined)}
        </DropdownSurface>
        {errorNode}
      </div>
    );
  }

  // The control never renders chips for multi select — selected items are shown by the consumer.
  const selectedOption = isMulti ? undefined : selectValue[0];
  const getSelectedLabel = (): ReactNode => {
    if (!selectedOption) return null;
    if (formatOptionLabel) {
      return formatOptionLabel(selectedOption, { context: 'value', selectValue, inputValue: searchText });
    }

    return getOptionLabel ? getOptionLabel(selectedOption) : selectedOption.label;
  };
  const selectedLabel = getSelectedLabel();

  return (
    <div
      className={classnames(
        styles['dropdown-list'],
        label && styles['dropdown-list_labeled'],
        isDisabled && styles['dropdown-list_disabled'],
        className,
      )}
    >
      {labelNode}
      <Dropdown
        isDisabled={isDisabled}
        direction={placement === 'left' ? 'right' : undefined}
        className={styles['dropdown-list__dropdown']}
        toggleProps={{
          className: styles['dropdown-list__toggle'],
          'aria-label': title || label,
        }}
        menuClassName={classnames(styles[`dropdown-list__menu_${controlSize}`], menuClassName)}
        renderToggle={(isOpen) => (controlSize === 'sm' ? (
          <DropdownControl
            title={title || selectedLabel || placeholder}
            isOpen={isOpen}
            className={controlClassName}
          />
        ) : (
          <span
            className={classnames(
              styles['dropdown-list__control'],
              isOpen && styles['dropdown-list__control_open'],
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
              className={classnames(styles['dropdown-list__arrow'], isOpen && styles['dropdown-list__arrow_open'])}
            />
          </span>
        ))}
      >
        {({ closeDropdown }) => renderMenu(closeDropdown)}
      </Dropdown>
      {errorNode}
    </div>
  );
}

export function FormikDropdownList(
  props: IDropdownListProps<TDropdownOptionBase> & FieldHookConfig<string>,
) {
  const { name, options, type } = props;
  const [field, meta, { setValue }] = useField(name);

  return (
    <DropdownList
      {...props}
      onChange={({ value }: TDropdownOptionBase) => setValue(String(value))}
      value={flattenOptions(options).find((option) => option.value === field.value)}
      {...(meta.touched && meta.error && type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}

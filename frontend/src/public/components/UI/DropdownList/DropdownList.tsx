import React, { ReactNode, useRef, useState } from 'react';
import classnames from 'classnames';
import { FieldHookConfig, useField } from 'formik';
import OutsideClickHandler from 'react-outside-click-handler';
import Select, { ActionMeta, InputActionMeta, OnChangeValue } from 'react-select';

import { createDropdownListComponents } from './DropdownListMenu';
import {
  IDropdownListProps,
  IDropdownListSelectComponentsProps,
  TControlSize,
  TDropdownOptionBase,
  TDropdownOptionGroup,
  TPlacement,
} from './types';
import { flattenOptions, getDefaultOptionValue, getOptionSearchText, toArray } from './utils';

import styles from './DropdownList.css';

const getReactSelectStyles = (staticMenu: boolean, controlSize: TControlSize, placement?: TPlacement) => ({
  container: (base: any) => ({ ...base, width: '100%' }),
  control: (base: any) => ({
    ...base,
    minHeight: 0,
    border: 0,
    boxShadow: 'none',
    backgroundColor: controlSize === 'sm' ? 'transparent' : 'var(--pneumatic-color-white)',
  }),
  menu: (base: any) => ({
    ...base,
    ...(staticMenu ? { position: 'relative', top: 'auto' } : null),
    ...(placement === 'left' && !staticMenu ? { left: 'auto', right: 0 } : null),
    margin: 0,
    zIndex: 1000,
    width: 'auto',
    minWidth: '100%',
    backgroundColor: 'transparent',
    boxShadow: 'none',
  }),
  menuList: (base: any) => ({ ...base, padding: 0, maxHeight: 'none' }),
  group: (base: any) => ({ ...base, padding: 0 }),
  groupHeading: (base: any) => ({ ...base, margin: 0, padding: 0 }),
  option: (base: any) => ({ ...base, padding: 0, backgroundColor: 'transparent' }),
});

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
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [uncontrolledValue, setUncontrolledValue] = useState<TOption | TOption[] | null>(defaultValue ?? null);
  const isControlled = value !== undefined;
  const currentValue = isControlled ? value : uncontrolledValue;
  const selectValue = toArray(currentValue);
  const optionKey = (option: TOption) => (getOptionValue ? getOptionValue(option) : getDefaultOptionValue(option));

  const handleSearchChange = (nextSearch: string) => {
    setSearchText(nextSearch);
    onInputChange?.(nextSearch);
  };

  const handleInputChange = (nextSearch: string, { action }: InputActionMeta) => {
    if (action === 'input-change') handleSearchChange(nextSearch);
    if (action === 'set-value' || action === 'menu-close') handleSearchChange('');

    return nextSearch;
  };

  const getSelectedLabel = (): ReactNode => {
    if (isMulti || !selectValue[0]) return null;
    if (formatOptionLabel) {
      return formatOptionLabel(selectValue[0], { context: 'value', selectValue, inputValue: searchText });
    }

    return getOptionLabel ? getOptionLabel(selectValue[0]) : selectValue[0].label;
  };

  const handleChange = (newValue: OnChangeValue<TOption, boolean>, actionMeta: ActionMeta<TOption>) => {
    const changedOption =
      actionMeta.option || (Array.isArray(newValue) ? undefined : (newValue as TOption | null)) || undefined;
    if (changedOption?.onClick) {
      changedOption.onClick();
      handleSearchChange('');
      return;
    }

    const nextValue = isMulti ? toArray(newValue as TOption[]) : (newValue as TOption | null);
    if (!isControlled) setUncontrolledValue(nextValue);
    onChange?.(nextValue, { action: actionMeta.action as 'select-option' | 'deselect-option', option: changedOption });
    if (closeMenuOnSelect ?? !isMulti) setIsMenuOpen(false);
    handleSearchChange('');
  };

  const selectedLabel = getSelectedLabel();
  const selectOptionValue = isMulti ? selectValue : selectValue[0] || null;
  const componentsPropsRef = useRef<IDropdownListSelectComponentsProps<TOption>>();
  componentsPropsRef.current = {
    controlSize,
    title,
    label,
    isMulti,
    placeholder,
    selectedLabel,
    selectValue,
    searchText,
    isSearchable,
    isDisabled,
    staticMenu,
    isMenuOpen: staticMenu || isMenuOpen,
    onToggleMenu: () => setIsMenuOpen((current) => !current),
    onCloseMenu: () => setIsMenuOpen(false),
    placement,
    errorMessage,
    controlClassName,
    menuClassName,
    noOptionsMessage,
    getOptionLabel,
    formatOptionLabel,
    onSearchChange: handleSearchChange,
  };

  const selectComponentsRef = useRef<ReturnType<typeof createDropdownListComponents<TOption>>>();
  if (!selectComponentsRef.current) {
    selectComponentsRef.current = createDropdownListComponents<TOption>(
      () => componentsPropsRef.current as IDropdownListSelectComponentsProps<TOption>,
    );
  }
  const selectComponents = selectComponentsRef.current;

  const labelNode = label ? (
    <p className={styles['dropdown-list__label']}>
      {label}
      {isRequired && <span className={styles['dropdown-list__required']}>*</span>}
    </p>
  ) : null;
  const errorNode = errorMessage ? <p className={styles['dropdown-list__error']}>{errorMessage}</p> : null;

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
      <OutsideClickHandler
        display="contents"
        disabled={staticMenu || !isMenuOpen}
        onOutsideClick={() => setIsMenuOpen(false)}
      >
        <Select<TOption, boolean, TDropdownOptionGroup<TOption>>
          options={options}
          value={selectOptionValue}
          inputValue={searchText}
          onInputChange={handleInputChange}
          onChange={handleChange}
          isMulti={isMulti}
          isSearchable={false}
          isDisabled={isDisabled && !staticMenu}
          closeMenuOnSelect={closeMenuOnSelect ?? !isMulti}
          hideSelectedOptions={false}
          controlShouldRenderValue={false}
          tabSelectsValue={false}
          isClearable={false}
          backspaceRemovesValue={false}
          styles={getReactSelectStyles(staticMenu, controlSize, placement)}
          menuIsOpen={staticMenu || isMenuOpen}
          onMenuOpen={() => setIsMenuOpen(true)}
          onMenuClose={() => setIsMenuOpen(false)}
          getOptionValue={(option) => optionKey(option) || ''}
          getOptionLabel={(option) => getOptionSearchText(option, getOptionLabel)}
          filterOption={(candidate, input) => {
            const option = candidate.data as TOption;
            const labelText = getOptionSearchText(option, getOptionLabel);
            if (filterOption) {
              return filterOption({ label: labelText, value: optionKey(option) || '', data: option }, input);
            }

            return labelText.toLowerCase().includes(input.toLowerCase());
          }}
          components={selectComponents}
        />
      </OutsideClickHandler>
      {errorNode}
    </div>
  );
}

export function FormikDropdownList(props: IDropdownListProps<TDropdownOptionBase> & FieldHookConfig<string>) {
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

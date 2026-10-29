import React, { useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import ReactSelect from 'react-select';
import type { CSSObjectWithLabel } from 'react-select';
import PerfectScrollbar from 'react-perfect-scrollbar';
import OutsideClickHandler from 'react-outside-click-handler';

import { ArrowDropdownIcon } from '../../icons';
import { ControlSM } from './ControlSM';
import { MenuSM } from './MenuSM';
import { MenuListSM } from './MenuListSM';
import { Option } from './Option';
import { formatCompactMultiOptionLabel, formatCompactOptionLabel } from './utils/formatCompactOptionLabel';
import { filterCompactOption } from './utils/filterCompactOption';

import '../../../assets/css/library/react-select.css';
import styles from './Select.css';
import type { IControlSMParams, ISelectProps, TControlSize, TSelectOption } from './types';

const MENU_PORTAL_STYLES = { menuPortal: (base: CSSObjectWithLabel) => ({ ...base, zIndex: 1080 }) };

export function Select<TOption extends TSelectOption>({
  controlSize = 'lg',
  controlVariant = 'muted',
  controlClassName,
  controlContent,
  Icon,
  onClear,
  label,
  title,
  className,
  isMulti,
  ...restProps
}: ISelectProps<TOption>) {
  const { messages, formatMessage } = useIntl();
  const [isOpen, setIsOpen] = useState(false);
  const [filterValue, setFilterValue] = useState('');
  const { errorMessage } = restProps;
  const errorText = errorMessage && messages[errorMessage] ? formatMessage({ id: errorMessage }) : errorMessage;

  const handleInputChange = (inputValue: string, action: any) => {
    if (action.action === 'set-value' && !(isMulti && controlSize === 'sm')) {
      setFilterValue('');
    }
    if (action.action === 'input-change') {
      setFilterValue(inputValue);
    }
    if (restProps.onInputChange) {
      restProps.onInputChange(inputValue, action);
    }
  };

  const components = getComponents(controlSize, Boolean(restProps.isStaticMenu));
  const controlSm: IControlSMParams = {
    title: title || '',
    isOpen,
    isDisabled: Boolean(restProps.isDisabled),
    variant: controlVariant,
    className: controlClassName,
    Icon,
    content: controlContent,
    onToggle: setIsOpen,
    onClear,
  };

  const handleOutsideClick = (event: MouseEvent) => {
    if (!(event.target as Element | null)?.closest?.('.react-select__menu-portal')) setIsOpen(false);
  };

  const handleChange = (value: unknown, action: unknown) => {
    if (controlSize === 'sm' && !isMulti) setIsOpen(false);
    restProps.onChange?.(value, action);
  };

  const handleMenuClose = () => {
    if (controlSize === 'sm') setIsOpen(false);
    restProps.onMenuClose?.();
  };

  if (label && controlSize === 'lg') {
    return (
      <div className={classnames('react-select', restProps.isDisabled && 'is-disabled', className)}>
        <div className={classnames(styles['select-lg__control'], label && styles['is-label'])}>
          {label && (
            <p className={styles['select-lg__label']}>
              {label}
              {restProps.isRequired && <span className={styles['is-required']}>*</span>}
            </p>
          )}

          <ReactSelect
            isMulti={isMulti}
            closeMenuOnSelect={!isMulti}
            hideSelectedOptions={false}
            controlShouldRenderValue={!isMulti}
            tabSelectsValue={false}
            isClearable={false}
            classNamePrefix="react-select"
            components={components}
            onInputChange={handleInputChange}
            className={classnames(restProps.errorMessage && styles['has-error'])}
            {...restProps}
          />

          {errorText && <p className={styles['error-text']}>{errorText}</p>}
        </div>
      </div>
    );
  }

  return (
    <div
      className={classnames(
        'react-select',
        restProps.isDisabled && 'is-disabled',
        className,
        restProps.isStaticMenu && 'is-static',
      )}
    >
      {label && (
        <p className={styles['select-lg__label']}>
          {label}
          {restProps.isRequired && <span className={styles['is-required']}>*</span>}
        </p>
      )}
      <OutsideClickHandler onOutsideClick={handleOutsideClick}>
        <ReactSelect
          isMulti={isMulti}
          closeMenuOnSelect={!isMulti}
          hideSelectedOptions={false}
          controlShouldRenderValue={!isMulti}
          tabSelectsValue={false}
          isClearable={false}
          classNamePrefix="react-select"
          components={components}
          inputValue={filterValue}
          onInputChange={handleInputChange}
          styles={MENU_PORTAL_STYLES}
          {...(controlSize === 'sm' && {
            formatOptionLabel: isMulti ? formatCompactMultiOptionLabel : formatCompactOptionLabel,
            filterOption: filterCompactOption,
          })}
          {...restProps}
          {...{ controlSm }}
          onChange={handleChange}
          onMenuClose={handleMenuClose}
          {...(controlSize === 'sm' && !restProps.isStaticMenu && { menuIsOpen: isOpen && !restProps.isDisabled })}
          {...(restProps.isStaticMenu && { menuIsOpen: true })}
        />
      </OutsideClickHandler>
      {errorText && <p className={styles['error-text']}>{errorText}</p>}
    </div>
  );
}

const DropdownIndicator = ({ isDisabled }: any) => {
  return !isDisabled ? <ArrowDropdownIcon /> : null;
};

const MenuListLG = ({ selectProps, ...props }: any) => {
  const ScrollBar = PerfectScrollbar as unknown as Function;

  return (
    <ScrollBar className={styles['select__scrollbar']} options={{ suppressScrollX: true, wheelPropagation: false }}>
      {props.children}
    </ScrollBar>
  );
};

const NullComponent = () => null;

const LG_COMPONENTS = {
  Option,
  DropdownIndicator,
  MenuList: MenuListLG,
  IndicatorSeparator: NullComponent,
};

const SM_COMPONENTS = {
  Menu: MenuSM,
  Option,
  Control: ControlSM,
  Input: NullComponent,
  ValueContainer: NullComponent,
  MenuList: MenuListSM,
};

const SM_STATIC_COMPONENTS = {
  Menu: MenuSM,
  Option,
  Control: NullComponent,
  ValueContainer: NullComponent,
  MenuList: MenuListSM,
};

function getComponents(controlSize: TControlSize, isStaticMenu: boolean) {
  if (controlSize === 'lg') return LG_COMPONENTS;

  return isStaticMenu ? SM_STATIC_COMPONENTS : SM_COMPONENTS;
}

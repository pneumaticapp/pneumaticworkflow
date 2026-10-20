import * as React from 'react';
import { useState } from 'react';
import classnames from 'classnames';
import Select, { components } from 'react-select';
import type { CSSObjectWithLabel } from 'react-select';
import { FieldHookConfig, useField } from 'formik';
import PerfectScrollbar from 'react-perfect-scrollbar';
import OutsideClickHandler from 'react-outside-click-handler';

import { ArrowDropdownIcon, ExpandIcon, RoundClearIconMd } from '../../icons';

import '../../../assets/css/library/react-select.css';
import styles from './DropdownList.css';

type TControlSize = 'lg' | 'sm';
type TControlVariant = 'muted' | 'accent';
type TPlacement = 'left' | 'right';

export type TDropdownOptionBase = {
  label: string | React.ReactNode;
  sourceId?: string | null;
  value?: string;
  onClick?: () => void;
};

interface IControlSMParams {
  title: string;
  isOpen: boolean;
  isDisabled: boolean;
  variant: TControlVariant;
  className?: string;
  Icon?(props: React.SVGAttributes<SVGElement>): JSX.Element;
  onToggle(isOpen: boolean): void;
}

export interface IDropdownListProps<TOption extends TDropdownOptionBase> extends Omit<
  React.ComponentProps<typeof Select>,
  'options' | 'onChange'
> {
  label?: string;
  options: TOption[];
  title?: string;
  controlSize?: TControlSize;
  className?: string;
  staticMenu?: boolean;
  placement?: TPlacement;
  onChange?: (value: any, action: any) => void;
  errorMessage?: string;
  isRequired?: boolean;
  controlVariant?: TControlVariant;
  controlClassName?: string;
  Icon?(props: React.SVGAttributes<SVGElement>): JSX.Element;
}

const MENU_PORTAL_STYLES = { menuPortal: (base: CSSObjectWithLabel) => ({ ...base, zIndex: 1080 }) };

export function DropdownList<TOption extends TDropdownOptionBase>({
  controlSize = 'lg',
  controlVariant = 'muted',
  controlClassName,
  Icon,
  label,
  title,
  className,
  isMulti,
  ...restProps
}: IDropdownListProps<TOption>) {
  const [isOpen, setIsOpen] = useState(false);
  const [filterValue, setFilterValue] = useState('');

  const handleInputChange = (inputValue: string, action: any) => {
    if (action.action === 'set-value') {
      setFilterValue('');
    }
    if (action.action === 'input-change') {
      setFilterValue(inputValue);
    }
    if (restProps.onInputChange) {
      restProps.onInputChange(inputValue, action);
    }
  };

  const componentsMap: { [key in TControlSize]: any } = {
    lg: {
      Option,
      DropdownIndicator,
      MenuList: MenuListLG,
      IndicatorSeparator: () => null,
    },
    sm: {
      Menu: MenuSM,
      Option,
      Control: !restProps.staticMenu
        ? ControlSM({
            title: title || '',
            isOpen,
            isDisabled: Boolean(restProps.isDisabled),
            variant: controlVariant,
            className: controlClassName,
            Icon,
            onToggle: setIsOpen,
          })
        : () => null,
      ...(!restProps.staticMenu && { Input: () => null }),
      ValueContainer: () => null,
      MenuList: MenuListSM,
    },
  };

  if (label && controlSize === 'lg') {
    return (
      <div className={classnames('react-select', restProps.isDisabled && 'is-disabled', className)}>
        <div className={classnames(styles['dropdownlist-lg__control'], label && styles['is-label'])}>
          {label && (
            <p className={styles['dropdownlist-lg__label']}>
              {label}
              {restProps.isRequired && <span className={styles['is-required']}>*</span>}
            </p>
          )}

          <Select
            isMulti={isMulti}
            closeMenuOnSelect={!isMulti}
            hideSelectedOptions={false}
            controlShouldRenderValue={!isMulti}
            tabSelectsValue={false}
            isClearable={false}
            classNamePrefix="react-select"
            components={componentsMap[controlSize]}
            onInputChange={handleInputChange}
            className={classnames(restProps.errorMessage && styles['has-error'])}
            {...restProps}
          />

          {restProps.errorMessage && <p className={styles['error-text']}>{restProps.errorMessage}</p>}
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
        restProps.staticMenu && 'is-static',
      )}
    >
      {label && (
        <p className={styles['dropdownlist-lg__label']}>
          {label}
          {restProps.isRequired && <span className={styles['is-required']}>*</span>}
        </p>
      )}
      <OutsideClickHandler onOutsideClick={() => setIsOpen(false)}>
        <Select
          isMulti={isMulti}
          closeMenuOnSelect={!isMulti}
          hideSelectedOptions={false}
          controlShouldRenderValue={!isMulti}
          tabSelectsValue={false}
          isClearable={false}
          classNamePrefix="react-select"
          components={componentsMap[controlSize]}
          inputValue={filterValue}
          onInputChange={handleInputChange}
          styles={MENU_PORTAL_STYLES}
          {...restProps}
          onChange={(value: unknown, action: unknown) => {
            if (controlSize === 'sm' && !isMulti) setIsOpen(false);
            restProps.onChange?.(value, action);
          }}
          {...(controlSize === 'sm' && !restProps.staticMenu && { menuIsOpen: isOpen })}
          {...(restProps.staticMenu && { menuIsOpen: true })}
        />
      </OutsideClickHandler>
      {restProps.errorMessage && <p className={styles['error-text']}>{restProps.errorMessage}</p>}
    </div>
  );
}

function ControlSM({ title, isOpen, isDisabled, variant, className, Icon, onToggle }: IControlSMParams) {
  return (props: any) => {
    return (
      <button
        ref={props.innerRef}
        type="button"
        disabled={isDisabled}
        className={classnames(
          'react-select_controlllll',
          styles['dropdownlist-sm__control'],
          variant === 'accent' && styles['dropdownlist-sm__control_accent'],
          isOpen && styles['is-open'],
          className,
        )}
        onClick={() => onToggle(!isOpen)}
      >
        {Icon && <Icon className={styles['dropdownlist-sm__icon']} />}
        <p className={styles['dropdownlist-sm__value']}>{title || props?.selectProps.value?.label}</p>
        <ExpandIcon className={classnames(styles['dropdownlist-sm__arrow'], isOpen && styles['is-open'])} />
      </button>
    );
  };
}

const DropdownIndicator = ({ isDisabled }: any) => {
  return !isDisabled ? <ArrowDropdownIcon /> : null;
};

const MenuSM = ({ children, ...props }: any) => {
  const customClassName = props.selectProps.classNames?.menuList?.(props);

  return (
    <div
      className={classnames(
        'react-select__menu-list',
        props.selectProps.staticMenu ? 'is-static' : 'is-sm',
        props.selectProps.placement === 'left' && 'is-left',
        customClassName,
      )}
    >
      <components.Menu {...props}>{children}</components.Menu>
    </div>
  );
};

const MenuListLG = ({ selectProps, ...props }: any) => {
  const ScrollBar = PerfectScrollbar as unknown as Function;

  return (
    <ScrollBar
      className={styles['dropdownlist__scrollbar']}
      options={{ suppressScrollX: true, wheelPropagation: false }}
    >
      {props.children}
    </ScrollBar>
  );
};

const MenuListSM = ({ selectProps, ...props }: any) => {
  const ScrollBar = PerfectScrollbar as unknown as Function;
  const { onInputChange, inputValue, onMenuInputFocus, placeholder, isSearchable } = selectProps;

  const ariaAttributes = {
    'aria-label': selectProps['aria-label'],
    'aria-labelledby': selectProps['aria-labelledby'],
  };

  return (
    <div>
      {isSearchable && (
        <div className={styles['dropdownlist-sm__search']}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) =>
              onInputChange(e.currentTarget.value, {
                action: 'input-change',
              })
            }
            // When opening sm dropdown, set the autofocus on the search field

            autoFocus
            onMouseDown={(e) => e.stopPropagation()}
            onTouchEnd={(e) => e.stopPropagation()}
            onFocus={onMenuInputFocus}
            placeholder={placeholder}
            {...ariaAttributes}
          />
          {inputValue && (
            <button
              className={styles['dropdownlist-sm__clear']}
              type="button"
              aria-label="button"
              onClick={() =>
                onInputChange('', {
                  action: 'input-change',
                })
              }
            >
              <RoundClearIconMd />
            </button>
          )}
        </div>
      )}

      <ScrollBar
        className={styles['dropdownlist__scrollbar']}
        options={{ suppressScrollX: true, wheelPropagation: false }}
      >
        {props.children}
      </ScrollBar>
    </div>
  );
};

const Option = (props: any) => {
  const { innerProps, data } = props;
  if (data.onClick) innerProps.onClick = data.onClick;

  return <components.Option {...props} />;
};

export function FormikDropdownList(props: IDropdownListProps<TDropdownOptionBase> & FieldHookConfig<string>) {
  const { name, options, type } = props;
  const [field, meta, { setValue }] = useField(name);

  const onChange = ({ value }: any) => setValue(value);

  return (
    <DropdownList
      {...props}
      onChange={onChange}
      value={options.find((option) => option.value === field.value)}
      {...(meta.touched && meta.error && type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}

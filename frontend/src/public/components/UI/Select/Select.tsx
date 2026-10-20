import * as React from 'react';
import { useState } from 'react';
import classnames from 'classnames';
import ReactSelect, { components } from 'react-select';
import type { CSSObjectWithLabel, FormatOptionLabelMeta } from 'react-select';
import { FieldHookConfig, useField } from 'formik';
import PerfectScrollbar from 'react-perfect-scrollbar';
import OutsideClickHandler from 'react-outside-click-handler';

import { ArrowDropdownIcon, ClearIcon, ExpandIcon, RoundClearIconMd } from '../../icons';
import { Checkbox } from '../Fields/Checkbox';
import { Skeleton } from '../Skeleton';

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
  const [isOpen, setIsOpen] = useState(false);
  const [filterValue, setFilterValue] = useState('');

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

  const components = getComponents(controlSize, Boolean(restProps.staticMenu));
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
        <p className={styles['select-lg__label']}>
          {label}
          {restProps.isRequired && <span className={styles['is-required']}>*</span>}
        </p>
      )}
      <OutsideClickHandler
        onOutsideClick={(event: MouseEvent) => {
          if (!(event.target as Element | null)?.closest?.('.react-select__menu-portal')) setIsOpen(false);
        }}
      >
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
          onChange={(value: unknown, action: unknown) => {
            if (controlSize === 'sm' && !isMulti) setIsOpen(false);
            restProps.onChange?.(value, action);
          }}
          {...(controlSize === 'sm' && !restProps.staticMenu && { menuIsOpen: isOpen && !restProps.isDisabled })}
          {...(restProps.staticMenu && { menuIsOpen: true })}
        />
      </OutsideClickHandler>
      {restProps.errorMessage && <p className={styles['error-text']}>{restProps.errorMessage}</p>}
    </div>
  );
}

function ControlSM(props: any) {
  const { title, isOpen, isDisabled, variant, className, Icon, content, onToggle, onClear }: IControlSMParams =
    props.selectProps.controlSm;

  if (content) {
    return (
      <button
        ref={props.innerRef}
        type="button"
        disabled={isDisabled}
        className={classnames(styles['select-sm__control-custom'], className)}
        onClick={() => onToggle(!isOpen)}
      >
        {content}
      </button>
    );
  }

  return (
    <button
      ref={props.innerRef}
      type="button"
      disabled={isDisabled}
      className={classnames(
        'react-select_controlllll',
        styles['select-sm__control'],
        variant === 'accent' && styles['select-sm__control_accent'],
        isOpen && styles['is-open'],
        className,
      )}
      onClick={() => onToggle(!isOpen)}
    >
      {Icon && <Icon className={styles['select-sm__icon']} />}
      <p className={styles['select-sm__value']}>{title || props?.selectProps.value?.label}</p>
      {onClear ? (
        <span
          role="button"
          tabIndex={0}
          aria-label="Clear selected options"
          className={styles['select-sm__clear-value']}
          onClick={(event) => {
            event.stopPropagation();
            onClear();
          }}
          onKeyDown={(event) => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            event.stopPropagation();
            onClear();
          }}
        >
          <ClearIcon />
        </span>
      ) : (
        <ExpandIcon className={classnames(styles['select-sm__arrow'], isOpen && styles['is-open'])} />
      )}
    </button>
  );
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
        props.selectProps.isMulti && 'is-multi',
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
    <ScrollBar className={styles['select__scrollbar']} options={{ suppressScrollX: true, wheelPropagation: false }}>
      {props.children}
    </ScrollBar>
  );
};

const SKELETON_ROW_WIDTHS = ['80%', '60%', '80%', '60%', '70%'];

function formatCompactOptionLabel(data: unknown, { context }: FormatOptionLabelMeta<unknown>) {
  const option = data as TSelectOption;
  if (context !== 'menu') return option.label;

  return (
    <span className={styles['select-sm__option']}>
      <span className={styles['select-sm__option-label']}>{option.label}</span>
      {option.count !== undefined && <span className={styles['select-sm__option-count']}>{option.count}</span>}
    </span>
  );
}

function formatCompactMultiOptionLabel(data: unknown, meta: FormatOptionLabelMeta<unknown>) {
  const option = data as TSelectOption;
  const content = formatCompactOptionLabel(data, meta);
  if (meta.context !== 'menu' || !option.value) return content;

  return (
    <span className={styles['select-sm__option-check']}>
      <Checkbox
        checked={(meta.selectValue as TSelectOption[]).some(({ value }) => value === option.value)}
        title={content}
        onChange={() => {}}
      />
    </span>
  );
}

function filterCompactOption({ label, data }: { label: string; data: unknown }, input: string) {
  const option = data as TSelectOption;
  const searchText = option.searchByText ?? (typeof option.label === 'string' ? option.label : label);

  return !input || searchText.toLowerCase().includes(input.toLowerCase());
}

const MenuListSM = ({ selectProps, ...props }: any) => {
  const ScrollBar = PerfectScrollbar as unknown as Function;
  const { onInputChange, inputValue, onMenuInputFocus, placeholder, isSearchable } = selectProps;

  const ariaAttributes = {
    'aria-label': selectProps['aria-label'],
    'aria-labelledby': selectProps['aria-labelledby'],
  };

  return (
    <div>
      {isSearchable && !selectProps.isLoading && (
        <div className={styles['select-sm__search']}>
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
              className={styles['select-sm__clear']}
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

      <ScrollBar className={styles['select__scrollbar']} options={{ suppressScrollX: true, wheelPropagation: false }}>
        {selectProps.isLoading
          ? SKELETON_ROW_WIDTHS.map((width, index) => (
              <div key={index} className={styles['select-sm__skeleton']}>
                <Skeleton display="block" height="2.4rem" width={width} />
              </div>
            ))
          : props.children}
      </ScrollBar>
    </div>
  );
};

const Option = (props: any) => {
  const { innerProps, data } = props;
  if (data.onClick) innerProps.onClick = data.onClick;

  return <components.Option {...props} />;
};

export function FormikSelect(
  props: Omit<ISelectProps<TSelectOption>, 'options'> & {
    options: TSelectOption[];
  } & FieldHookConfig<string>,
) {
  const { name, options, type } = props;
  const [field, meta, { setValue }] = useField(name);

  const onChange = ({ value }: any) => setValue(value);

  return (
    <Select
      {...props}
      onChange={onChange}
      value={options.find((option) => option.value === field.value)}
      {...(meta.touched && meta.error && type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}

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

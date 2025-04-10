import React, { useState } from 'react';
import classnames from 'classnames';
import Select, { components } from 'react-select';
import { FieldHookConfig, useField } from 'formik';
import PerfectScrollbar from 'react-perfect-scrollbar';
import OutsideClickHandler from 'react-outside-click-handler';

import { ArrowDropdownIcon, ExpandIcon, RoundClearIconMd } from '../../icons';

import '../../../assets/css/library/react-select.css';
import styles from './DropdownList.css';

type TControlSize = 'lg' | 'sm';
type TPlacement = 'left' | 'right';

export type TDropdownOptionBase = {
  label: string | React.ReactNode;
  sourceId?: string | null;
  value?: string;
  onClick?: () => void;
};

export interface IDropdownListProps<TOption extends TDropdownOptionBase>
  extends Omit<React.ComponentProps<typeof Select>, 'options' | 'onChange'> {
  label?: string;
  options: TOption[];
  title?: string;
  controlSize?: TControlSize;
  className?: string;
  staticMenu?: boolean;
  placement?: TPlacement;
  onChange?: (value: any, action: any) => void;
}

export function DropdownList<TOption extends TDropdownOptionBase>({
  controlSize = 'lg',
  label,
  title,
  className,
  isMulti,
  ...restProps
}: IDropdownListProps<TOption>) {
  const [isOpen, setIsOpen] = useState(false);
  const [filterValue, setFilterValue] = useState('');

  const handleInputChange = (inputValue: string, action: any) => {
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
      Input,
    },
    sm: {
      Menu: MenuSM,
      Option,
      Control: !restProps.staticMenu ? ControlSM(title || '', isOpen, setIsOpen) : () => null,
      ...(!restProps.staticMenu && { Input: () => null }),
      ValueContainer: () => null,
      MenuList: MenuListSM,
    },
  };

  if (label && controlSize === 'lg') {
    return (
      <div className={classnames('react-select', className)}>
        <div className={classnames(styles['dropdownlist-lg__control'], label && styles['is-label'])}>
          {label && <p className={styles['dropdownlist-lg__label']}>{label}</p>}

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
            {...restProps}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={classnames('react-select', className, restProps.staticMenu && 'is-static')}>
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
          {...restProps}
          {...(controlSize === 'sm' && !restProps.staticMenu && { menuIsOpen: isOpen })}
          {...(restProps.staticMenu && { menuIsOpen: true })}
        />
      </OutsideClickHandler>
    </div>
  );
}

function Input({ autoComplete, ...rest }: any) {
  return <components.Input {...rest} aria-autocomplete="none" />;
}

function ControlSM(title: string, isOpen: boolean, onClick: (isOpen: boolean) => void) {
  return (props: any) => {
    return (
      <button
        type="button"
        className={classnames(
          'react-select_controlllll',
          styles['dropdownlist-sm__control'],
          isOpen && styles['is-open'],
        )}
        onClick={() => onClick(!isOpen)}
      >
        <p className={styles['dropdownlist-sm__value']}>{title || props?.selectProps.value.label}</p>
        <ExpandIcon className={classnames(styles['dropdownlist-sm__arrow'], isOpen && styles['is-open'])} />
      </button>
    );
  };
}

const DropdownIndicator = () => <ArrowDropdownIcon />;

const MenuSM = ({ children, ...props }: any) => {
  return (
    <div
      className={classnames(
        'react-select__menu-list',
        props.selectProps.staticMenu ? 'is-static' : 'is-sm',
        props.selectProps.placement === 'left' && 'is-left',
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
            // eslint-disable-next-line jsx-a11y/no-autofocus
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

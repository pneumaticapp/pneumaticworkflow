import * as React from 'react';
import classnames from 'classnames';
import { components } from 'react-select';
import type { ControlProps, DropdownIndicatorProps, GroupBase, MenuListProps, OptionProps } from 'react-select';
import PerfectScrollbar from 'react-perfect-scrollbar';

import { ArrowDropdownIcon, ExpandIcon, RoundClearIconMd } from '../../icons';

import type { TDropdownOptionBase } from './types';

import styles from './DropdownList.css';

export function ControlSM(title: string, isOpen: boolean, onClick: (isOpen: boolean) => void) {
  return ({ selectProps: { value } }: ControlProps<TDropdownOptionBase, boolean>) => {
    const selectedLabel = value && 'label' in value ? value.label : null;

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
        <p className={styles['dropdownlist-sm__value']}>{title || selectedLabel}</p>
        <ExpandIcon className={classnames(styles['dropdownlist-sm__arrow'], isOpen && styles['is-open'])} />
      </button>
    );
  };
}

export const DropdownIndicator = ({ isDisabled }: DropdownIndicatorProps<TDropdownOptionBase, boolean>) => {
  return !isDisabled ? <ArrowDropdownIcon /> : null;
};

export const MenuSM = ({ children, ...props }: any) => {
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

export const MenuListLG = ({ children }: MenuListProps<TDropdownOptionBase, boolean>) => {
  const ScrollBar = PerfectScrollbar as unknown as Function;

  return (
    <ScrollBar
      className={styles['dropdownlist__scrollbar']}
      options={{ suppressScrollX: true, wheelPropagation: false }}
    >
      {children}
    </ScrollBar>
  );
};

export const MenuListSM = ({ children, selectProps }: MenuListProps<TDropdownOptionBase, boolean>) => {
  const ScrollBar = PerfectScrollbar as unknown as Function;
  const {
    onInputChange,
    inputValue,
    placeholder,
    isSearchable,
    'aria-label': ariaLabel,
    'aria-labelledby': ariaLabelledBy,
  } = selectProps;

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
                prevInputValue: inputValue,
              })
            }
            // When opening sm dropdown, set the autofocus on the search field

            autoFocus
            onMouseDown={(e) => e.stopPropagation()}
            onTouchEnd={(e) => e.stopPropagation()}
            placeholder={typeof placeholder === 'string' ? placeholder : undefined}
            aria-label={ariaLabel}
            aria-labelledby={ariaLabelledBy}
          />
          {inputValue && (
            <button
              className={styles['dropdownlist-sm__clear']}
              type="button"
              aria-label="button"
              onClick={() =>
                onInputChange('', {
                  action: 'input-change',
                  prevInputValue: inputValue,
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
        {children}
      </ScrollBar>
    </div>
  );
};

export const Option = (props: OptionProps<TDropdownOptionBase, boolean>) => {
  const { innerProps, data } = props;
  if (data.onClick) innerProps.onClick = data.onClick;

  return <components.Option<TDropdownOptionBase, boolean, GroupBase<TDropdownOptionBase>> {...props} />;
};

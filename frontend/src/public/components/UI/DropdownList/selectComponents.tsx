import * as React from 'react';
import classnames from 'classnames';
import { components } from 'react-select';
import PerfectScrollbar from 'react-perfect-scrollbar';

import { ArrowDropdownIcon, ExpandIcon, RoundClearIconMd } from '../../icons';

import styles from './DropdownList.css';

export function ControlSM(title: string, isOpen: boolean, onClick: (isOpen: boolean) => void) {
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

export const DropdownIndicator = ({ isDisabled }: any) => {
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

export const MenuListLG = ({ selectProps, ...props }: any) => {
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

export const MenuListSM = ({ selectProps, ...props }: any) => {
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

export const Option = (props: any) => {
  const { innerProps, data } = props;
  if (data.onClick) innerProps.onClick = data.onClick;

  return <components.Option {...props} />;
};

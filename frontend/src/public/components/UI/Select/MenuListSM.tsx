import * as React from 'react';
import PerfectScrollbar from 'react-perfect-scrollbar';

import { RoundClearIconMd } from '../../icons';
import { Skeleton } from '../Skeleton';

import styles from './Select.css';

const SKELETON_ROW_WIDTHS = ['80%', '60%', '80%', '60%', '70%'];

export function MenuListSM({ selectProps, ...props }: any) {
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
}

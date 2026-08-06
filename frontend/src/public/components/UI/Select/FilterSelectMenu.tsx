import React, { ChangeEvent, KeyboardEvent, ReactNode } from 'react';
import classnames from 'classnames';
import PerfectScrollbar from 'react-perfect-scrollbar';

import { Checkbox } from '../Fields/Checkbox';
import { InputField } from '../Fields/InputField';
import { Skeleton } from '../Skeleton';
import { TOptionBase } from './types';

import styles from './Select.css';

const ScrollBar = PerfectScrollbar as unknown as Function;
const SKELETON_ROWS = [
  { id: 'first', width: '80%' },
  { id: 'second', width: '60%' },
  { id: 'third', width: '80%' },
  { id: 'fourth', width: '60%' },
  { id: 'fifth', width: '70%' },
];

interface IFilterSelectMenuProps<IdKey extends string, LabelKey extends string, TOption extends TOptionBase<IdKey, LabelKey>> {
  options: Array<TOption | string>;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  selectedOptionId: number | string | null | undefined;
  isMultiple: boolean;
  isLoading?: boolean;
  isSearchShown?: boolean;
  searchText: string;
  searchPlaceholder?: string;
  placeholderText: string;
  noValueLabel?: string;
  selectAllLabel?: string;
  isSelectAll: boolean;
  isSelected(option: TOption): boolean;
  onSearchChange(event: ChangeEvent<HTMLInputElement>): void;
  onClearSearch(): void;
  onReset(): void;
  onSelectAll(): void;
  onSelect(option: TOption): void;
  closeDropdown(): void;
}

const handleKeyboardAction = (event: KeyboardEvent, action: () => void) => {
  if (event.key !== 'Enter' && event.key !== ' ') return;
  event.preventDefault();
  action();
};

export function FilterSelectMenu<IdKey extends string, LabelKey extends string, TOption extends TOptionBase<IdKey, LabelKey>>({
  options,
  optionIdKey,
  optionLabelKey,
  selectedOptionId,
  isMultiple,
  isLoading,
  isSearchShown,
  searchText,
  searchPlaceholder,
  placeholderText,
  noValueLabel,
  selectAllLabel,
  isSelectAll,
  isSelected,
  onSearchChange,
  onClearSearch,
  onReset,
  onSelectAll,
  onSelect,
  closeDropdown,
}: IFilterSelectMenuProps<IdKey, LabelKey, TOption>) {
  if (isLoading) {
    return (
      <div className={styles['dropdown-menu__skeleton']}>
        {SKELETON_ROWS.map(({ id, width }) => (
          <div
            key={id}
            className={classnames(
              styles['dropdown-menu__skeleton-item'],
              id === 'fifth' && styles['dropdown-menu__skeleton-item_last'],
            )}
          >
            <Skeleton display="block" height="2.4rem" width={width} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <>
      {isSearchShown && (
        <>
          <div className={styles['sorting-item__search']}>
            <InputField
              value={searchText}
              onChange={onSearchChange}
              className={styles['search__input']}
              onClear={onClearSearch}
              fieldSize="md"
              autoFocus
              autoComplete="one-time-code"
              name="filter-select-search"
              placeholder={searchPlaceholder}
            />
          </div>
          <hr className={styles['search__separator']} />
        </>
      )}
      <ScrollBar className={styles['dropdown-menu__scrollbar']} options={{ suppressScrollX: true, wheelPropagation: false }}>
        {!options.length && (
          <div className={classnames(styles['value-item'], styles['value-item__disabled'])}>
            <span className={styles['dropdown-item__text_stub']}>{placeholderText}</span>
          </div>
        )}
        {selectedOptionId !== null && noValueLabel && (
          <button type="button" className={styles['value-item']} onClick={onReset}>{noValueLabel}</button>
        )}
        {isMultiple && selectAllLabel && (
          <div
            role="menuitemcheckbox"
            aria-checked={isSelectAll}
            aria-label={selectAllLabel}
            tabIndex={0}
            className={classnames(styles['value-item'], styles['value-item__select-all'])}
            onClick={onSelectAll}
            onKeyDown={(event) => handleKeyboardAction(event, onSelectAll)}
          >
            <Checkbox
              readOnly
              checked={isSelectAll}
              title={<span>{selectAllLabel}</span>}
              onClick={onSelectAll}
              containerClassName={styles['dropdown-item-check']}
              labelClassName={styles['dropdown-item-check__label']}
              titleClassName={styles['dropdown-item-check__title']}
            />
          </div>
        )}
        {options.map((option) => {
          if (typeof option === 'string') {
            return <div key={option} className={styles['dropdown-item-content__title']}>{option}</div>;
          }

          const content: ReactNode = (
            <div className={styles['dropdown-item-content']}>
              <div className={styles['dropdown-item-content__text']}>{option[optionLabelKey]}</div>
              {option.count !== undefined && <span className={styles['dropdown-item-content__count']}>{option.count}</span>}
            </div>
          );
          const key = `${option.type || ''}-${option[optionIdKey]}`;
          const select = () => {
            onSelect(option);
            if (!isMultiple) closeDropdown();
          };

          return isMultiple ? (
            <div
              role="menuitemcheckbox"
              aria-checked={isSelected(option)}
              aria-label={typeof option[optionLabelKey] === 'string' ? option[optionLabelKey] as string : option.searchByText}
              tabIndex={0}
              key={key}
              className={styles['value-item']}
              onClick={select}
              onKeyDown={(event) => handleKeyboardAction(event, select)}
            >
              <Checkbox
                readOnly
                checked={isSelected(option)}
                title={content}
                onClick={select}
                containerClassName={styles['dropdown-item-check']}
                labelClassName={styles['dropdown-item-check__label']}
                titleClassName={styles['dropdown-item-check__title']}
              />
            </div>
          ) : (
            <button type="button" role="menuitem" key={key} className={styles['value-item']} onClick={select}>{content}</button>
          );
        })}
      </ScrollBar>
    </>
  );
}

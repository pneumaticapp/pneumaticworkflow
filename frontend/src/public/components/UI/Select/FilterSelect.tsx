import React, { ChangeEvent, useState } from 'react';
import classnames from 'classnames';

import { ClearIcon, ExpandIcon } from '../../icons';
import { Dropdown } from '../Dropdown';
import { FilterSelectMenu } from './FilterSelectMenu';
import { TFilterSelectProps, TOptionBase } from './types';

import styles from './Select.css';

export function FilterSelect<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
>(props: TFilterSelectProps<IdKey, LabelKey, TOption>) {
  const {
    optionIdKey,
    optionLabelKey,
    isLoading,
    isSearchShown,
    isDisabled,
    noValueLabel,
    placeholderText,
    searchPlaceholder,
    toggleClassName,
    arrowClassName,
    menuClassName,
    isWideMenu,
    options,
    groupedOptions,
    flatGroupedOptions,
    containerClassname,
    selectAllLabel,
    resetFilter,
    Icon,
    isMultiple,
    onChange,
    selectedOptions,
    selectedOption,
    renderPlaceholder,
    positionFixed = false,
    getOptionSelectionKey,
  } = props;
  const [searchText, setSearchText] = useState('');
  const [isClearHovered, setClearHovered] = useState(false);
  const allOptions = flatGroupedOptions || options;
  const getSelectionKey = getOptionSelectionKey || ((option: TOption) => option[optionIdKey]);
  const isSelectAll = Boolean(isMultiple && allOptions.length && selectedOptions.length === allOptions.length);

  const filterOptions = (items: TOption[]) => {
    const query = searchText.toLowerCase();
    if (!query) return items;
    return items.filter((option) => {
      if (option.searchByText) return option.searchByText.toLowerCase().includes(query);
      const label = option[optionLabelKey];
      return typeof label !== 'string' || label.toLowerCase().includes(query);
    });
  };
  const filteredOptions: Array<TOption | string> = groupedOptions
    ? Array.from(groupedOptions.values()).flatMap((group) => {
      const items = filterOptions(group.options);
      return items.length ? [group.title, ...items] : [];
    })
    : filterOptions(options);

  const handleSelect = (option: TOption) => {
    if (option.customClickHandler) {
      option.customClickHandler();
      return;
    }
    if (!isMultiple) {
      onChange(option[optionIdKey]);
      return;
    }

    const key = getSelectionKey(option);
    const nextSelection = selectedOptions.includes(key)
      ? selectedOptions.filter((selected) => selected !== key)
      : [...selectedOptions, key];
    onChange(nextSelection, allOptions.filter((item) => nextSelection.includes(getSelectionKey(item))));
  };
  const handleSelectAll = () => {
    if (isSelectAll) {
      resetFilter();
      return;
    }
    if (isMultiple) onChange(allOptions.map(getSelectionKey), allOptions);
  };
  const hasSelectedOptions = Boolean(isMultiple && selectedOptions.length);

  return (
    <div
      className={classnames(
        styles['container'],
        containerClassname,
        isDisabled && styles['filter-select_disabled'],
      )}
    >
      <Dropdown
        direction="right"
        className={styles['filter-select__dropdown']}
        toggleProps={{
          className: classnames(
            styles['active-value'],
            toggleClassName,
            isClearHovered && styles['active-value_clear-hovered'],
          ),
        }}
        menuClassName={classnames(
          styles['dropdown-menu'],
          styles['dropdown-menu_search'],
          isWideMenu && styles['dropdown-menu_wide'],
          menuClassName,
          positionFixed && styles['dropdown-menu__position-fixed'],
        )}
        menuPositionFixed={positionFixed}
        isDisabled={isDisabled}
        renderToggle={() => (
          <>
            {Icon && <Icon className={styles['icon']} />}
            <span className={styles['active-value__text']}>{renderPlaceholder(allOptions)}</span>
            {!hasSelectedOptions && <ExpandIcon className={classnames(styles['expand-icon'], arrowClassName)} />}
          </>
        )}
      >
        {({ closeDropdown }) => (
          <FilterSelectMenu
            options={filteredOptions}
            optionIdKey={optionIdKey}
            optionLabelKey={optionLabelKey}
            selectedOptionId={selectedOption}
            isMultiple={Boolean(isMultiple)}
            isLoading={isLoading}
            isSearchShown={isSearchShown}
            searchText={searchText}
            searchPlaceholder={searchPlaceholder}
            placeholderText={placeholderText}
            noValueLabel={noValueLabel}
            selectAllLabel={selectAllLabel}
            isSelectAll={isSelectAll}
            isSelected={(option) => Boolean(isMultiple && selectedOptions.includes(getSelectionKey(option)))}
            onSearchChange={(event: ChangeEvent<HTMLInputElement>) => setSearchText(event.target.value)}
            onClearSearch={() => setSearchText('')}
            onReset={resetFilter}
            onSelectAll={handleSelectAll}
            onSelect={handleSelect}
            closeDropdown={closeDropdown}
          />
        )}
      </Dropdown>
      {hasSelectedOptions && (
        <button
          type="button"
          aria-label="Clear selected options"
          disabled={isDisabled}
          onClick={resetFilter}
          className={classnames(styles['clear-button'], arrowClassName)}
          onMouseEnter={() => setClearHovered(true)}
          onMouseLeave={() => setClearHovered(false)}
        >
          <ClearIcon />
        </button>
      )}
    </div>
  );
}

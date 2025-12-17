import React, { ChangeEvent, ReactNode, SVGAttributes, useState } from 'react';
import classnames from 'classnames';
import * as PerfectScrollbar from 'react-perfect-scrollbar';
import { DropdownItem, DropdownMenu, DropdownToggle, Dropdown } from 'reactstrap';

import OutsideClickHandler from 'react-outside-click-handler';
import { ClearIcon, ExpandIcon } from '../../icons';
import { isArrayWithItems } from '../../../utils/helpers';
import { Skeleton } from "../Skeleton";
import { Checkbox, InputField } from '..';

import styles from './Select.css';

const ScrollBar = PerfectScrollbar as unknown as Function;

type TOptionId = number | string | null;
export type TOptionBase<IdKey extends string, LabelKey extends string> = {
  [key in IdKey]: TOptionId;
} & {
  [key in LabelKey]: string | ReactNode;
} & {
  customClickHandler?(): void;
  areSubOptionsLoading?: boolean;
  count?: number;
  subTitle?: string;
  searchByText?: string;
  isTitle?: boolean;
};

interface IFilterSelectCommonProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> {
  isLoading?: boolean;
  options: TOption[];
  groupedOptions?: Map<number, { title: string; options: TOption[] }>;
  flatGroupedOptions?: TOption[];
  isSearchShown?: boolean;
  isDisabled?: boolean;
  noValueLabel?: string;
  placeholderText: string;
  searchPlaceholder?: string;
  toggleClassName?: string;
  arrowClassName?: string;
  menuClassName?: string;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  containerClassname?: string;
  selectAllLabel?: string;
  resetFilter(): void;
  selectAll?(): void;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  renderPlaceholder(options: TOption[]): string | JSX.Element;
}

interface IFilterSelectMultiOptionsProps {
  isMultiple: true;
  selectedOption?: never;
  selectedOptions: TOptionId[];
  onChange(optionIds: TOptionId[], option: any): void;
}

interface IFilterSelectSingleOptionsProps {
  isMultiple?: false;
  selectedOption: TOptionId;
  selectedOptions?: never;
  onChange(optionId: TOptionId | null): void;
}

type TFilterSelectProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> = IFilterSelectCommonProps<IdKey, LabelKey, TOption> &
  (IFilterSelectMultiOptionsProps | IFilterSelectSingleOptionsProps);

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
  } = props;
  const allOptions = flatGroupedOptions || options;
  const [searchText, setSearchText] = useState('');
  const [isSelectAll, setIsSelectAll] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isClearHovered, setClearHovered] = useState(false);

  const handleChange = (option: TOption) => () => {
    const { customClickHandler } = option;

    if (typeof customClickHandler === 'function') {
      customClickHandler();

      return;
    }

    const optionId = option[optionIdKey];

    if (!isMultiple) {
      onChange(optionId);

      return;
    }

    const newIsChecked = !selectedOptions.includes(optionId);

    const newSelectedOptions = newIsChecked
      ? [...selectedOptions, optionId]
      : selectedOptions.filter((selectedOptionElement) => selectedOptionElement !== optionId);

    const mapSelectedOption = allOptions.filter((item) => newSelectedOptions.includes(item[optionIdKey]));

    onChange(newSelectedOptions, mapSelectedOption);
  };

  const renderSearchInput = () => {
    if (!isSearchShown) {
      return null;
    }

    return (
      <>
        <div className={styles['sorting-item__search']}>
          <InputField
            value={searchText}
            onChange={handleChangeSearchText}
            className={styles['search__input']}
            onClear={handleClearSearchText}
            fieldSize="md"
            autoFocus
            placeholder={searchPlaceholder}
          />
        </div>
        <hr className={styles['search__separator']} />
      </>
    );
  };

  function getFilteredOptions(optionsParam: TOption[], normalizedSearchText: string): TOption[] {
    if (!normalizedSearchText) {
      return optionsParam;
    }

    return optionsParam.filter((option) => {
      if (option.searchByText) {
        return option.searchByText.toLowerCase().includes(normalizedSearchText);
      }

      const optionLabel = option[optionLabelKey];
      if (typeof optionLabel !== 'string') {
        return true;
      }

      return (optionLabel as string).toLowerCase().includes(normalizedSearchText);
    });
  }

  const getFilteredValues = () => {
    const normalizedSearchText = searchText.toLowerCase();

    if (!groupedOptions) {
      if (!searchText) {
        return options;
      }
      return getFilteredOptions(options, normalizedSearchText);
    }

    const filteredValues: (TOption | string)[] = [];
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    Array.from(groupedOptions.entries()).forEach(([_, group]) => {
      if (!searchText) {
        filteredValues.push(group.title, ...group.options);
      } else {
        const filteredOptions: TOption[] = getFilteredOptions(group.options, normalizedSearchText);
        if (filteredOptions.length === 0) {
          return;
        }

        filteredValues.push(group.title, ...filteredOptions);
      }
    });

    return filteredValues;
  };

  const renderDropdownList = () => {
    const foundValues = getFilteredValues();

    if (!isArrayWithItems(foundValues)) {
      return (
        <DropdownItem className={classnames('dropdown-item-sm', styles['value-item'])} disabled>
          <span className={styles['dropdown-item__text_stub']}>{placeholderText}</span>
        </DropdownItem>
      );
    }

    const renderResetOption = () => {
      if (!noValueLabel) {
        return null;
      }

      return (
        <DropdownItem
          className={classnames('dropdown-item-sm', styles['value-item'])}
          onClick={resetFilter}
          toggle={false}
        >
          <span>{noValueLabel}</span>
        </DropdownItem>
      );
    };

    const renderSelectAllOption = () => {
      if (!isMultiple || !selectAllLabel) {
        return null;
      }

      const handleSelectAll = () => {
        if (!isSelectAll) {
          setIsSelectAll(true);
          onChange(
            allOptions.map((option) => option[optionIdKey]),
            allOptions,
          );
        } else {
          setIsSelectAll(false);
          resetFilter();
        }
      };

      const areAllSelected =
        isMultiple &&
        Array.isArray(selectedOptions) &&
        allOptions.length > 0 &&
        selectedOptions.length === allOptions.length;

      return (
        <DropdownItem
          className={classnames('dropdown-item-sm', styles['value-item'], styles['value-item__select-all'])}
          onClick={handleSelectAll}
          toggle={false}
        >
          <Checkbox
            checked={isSelectAll || areAllSelected}
            title={<span>{selectAllLabel}</span>}
            onClick={(e) => e.stopPropagation()}
            onChange={() => {}}
            containerClassName={styles['dropdown-item-check']}
            labelClassName={styles['dropdown-item-check__label']}
            titleClassName={styles['dropdown-item-check__title']}
          />
        </DropdownItem>
      );
    };

    return (
      <>
        {selectedOption !== null && renderResetOption()}
        {renderSelectAllOption()}
        {foundValues.map((option) => {
          let label: ReactNode | null = null;

          if (typeof option !== 'string') {
            label = (
              <div className={styles['dropdown-item-content']}>
                <div className={styles['dropdown-item-content__text']}>{option[optionLabelKey]}</div>

                {typeof option.count !== 'undefined' && (
                  <span className={styles['dropdown-item-content__count']}>{option.count}</span>
                )}
              </div>
            );
          } else {
            label = <div className={styles['dropdown-item-content__title']}>{option}</div>;
          }

          return (
            <DropdownItem
              key={typeof option !== 'string' ? option[optionIdKey] : option}
              className={classnames('dropdown-item-sm', styles['value-item'])}
              onClick={typeof option !== 'string' ? handleChange(option) : () => {}}
              toggle={!isMultiple}
            >
              {isMultiple && typeof option !== 'string' ? (
                <Checkbox
                  checked={selectedOptions.includes(option[optionIdKey])}
                  title={label}
                  onClick={(e) => e.stopPropagation()}
                  onChange={() => {}}
                  containerClassName={styles['dropdown-item-check']}
                  labelClassName={styles['dropdown-item-check__label']}
                  titleClassName={styles['dropdown-item-check__title']}
                />
              ) : (
                label
              )}
            </DropdownItem>
          );
        })}
      </>
    );
  };

  const handleToggleDropdown = () => {
    if (isDisabled) {
      return;
    }
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleChangeSearchText = (e: ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  const handleClearSearchText = () => {
    setSearchText('');
  };

  if (isLoading) {
    const loaderClassName = classnames('dropdown-menu-right ml-sm-4 dropdown');

    return <Skeleton className={loaderClassName} />;
  }

  return (
    <OutsideClickHandler disabled={!isDropdownOpen} onOutsideClick={handleToggleDropdown}>
      <Dropdown
        className={classnames(
          'dropdown-menu-right dropdown',
          styles['container'],
          containerClassname,
          isDisabled && styles['filter-select_disabled'],
        )}
        toggle={handleToggleDropdown}
        isOpen={isDropdownOpen}
        onClick={(event) => event.stopPropagation()}
      >
        <DropdownToggle
          tag="button"
          disabled={!!isDisabled}
          className={classnames(
            styles['active-value'],
            toggleClassName,
            isClearHovered && styles['active-value_clear-hovered'],
          )}
        >
          {Icon && <Icon className={styles['icon']} />}
          <span className={styles['active-value__text']}>{renderPlaceholder(allOptions)}</span>
          {isMultiple && isArrayWithItems(selectedOptions) ? (
            <span
              aria-label="Clear selected options"
              aria-disabled={!!isDisabled}
              onClick={(e) => {
                if (isDisabled) {
                  return;
                }
                e.stopPropagation();
                resetFilter();
              }}
              className={classnames(styles['clear-button'], arrowClassName)}
              onMouseEnter={() => setClearHovered(true)}
              onMouseLeave={() => setClearHovered(false)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (isDisabled) {
                  return;
                }
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  e.stopPropagation();
                  resetFilter();
                }
              }}
            >
              <ClearIcon />
            </span>
          ) : (
            <ExpandIcon className={classnames(styles['expand-icon'], arrowClassName)} />
          )}
        </DropdownToggle>
        <DropdownMenu
          className={classnames(styles['dropdown-menu'], styles['dropdown-menu_search'], menuClassName)}
          modifiers={{ preventOverflow: { boundariesElement: 'window' } }}
        >
          {renderSearchInput()}
          <ScrollBar
            className={styles['dropdown-menu__scrollbar']}
            options={{ suppressScrollX: true, wheelPropagation: false }}
          >
            {renderDropdownList()}
          </ScrollBar>
        </DropdownMenu>
      </Dropdown>
    </OutsideClickHandler>
  );
}

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import * as PerfectScrollbar from 'react-perfect-scrollbar';
import { DropdownItem, DropdownMenu, DropdownToggle, Dropdown } from 'reactstrap';

import { ClearIcon, ExpandIcon } from '../../icons';
import { isArrayWithItems } from '../../../utils/helpers';
import { Skeleton } from '../../UI/Skeleton';
import { Checkbox, InputField } from '..';

import styles from './Select.css';
import OutsideClickHandler from 'react-outside-click-handler';

const ScrollBar = PerfectScrollbar as unknown as Function;

type TOptionId = number | string | null;
type TOptionBase<IdKey extends string, LabelKey extends string> = {
  [key in IdKey]: TOptionId;
} & {
  [key in LabelKey]: string | React.ReactNode;
} & {
  customClickHandler?(): void;
  areSubOptionsLoading?: boolean;
  count?: number;
  subTitle?: string;
  searchByText?: string;
};

interface IFilterSelectCommonProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> {
  isLoading?: boolean;
  options: TOption[];
  isSearchShown?: boolean;
  noValueLabel?: string;
  placeholderText: string;
  toggleClassName?: string;
  arrowClassName?: string;
  menuClassName?: string;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  containerClassname?: string;
  selectAllLabel?: string;
  resetFilter(): void;
  selectAll?(): void;
  Icon?(props: React.SVGAttributes<SVGElement>): JSX.Element;
  renderPlaceholder(options: TOption[]): string | JSX.Element;
}

interface IFilterSelectMultiOptionsProps {
  isMultiple: true;
  selectedOption?: never;
  selectedOptions: TOptionId[];
  onChange(optionIds: TOptionId[]): void;
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
    noValueLabel,
    placeholderText,
    toggleClassName,
    arrowClassName,
    menuClassName,
    options,
    containerClassname,
    selectAllLabel,
    resetFilter,
    Icon,
  } = props;

  const [searchText, setSearchText] = React.useState('');
  const [isSelectAll, setIsSelectAll] = React.useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const [isClearHovered, setClearHovered] = React.useState(false);

  const handleChange = (option: TOption) => () => {
    const { customClickHandler } = option;

    if (typeof customClickHandler === 'function') {
      customClickHandler();

      return;
    }

    const optionId = option[optionIdKey];

    if (!props.isMultiple) {
      props.onChange(optionId);

      return;
    }

    const newIsChecked = !props.selectedOptions.includes(optionId);

    const newSelectedOptions = newIsChecked
      ? [...props.selectedOptions, optionId]
      : props.selectedOptions.filter((selectedOption) => selectedOption !== optionId);

    props.onChange(newSelectedOptions);
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
          />
        </div>
        <hr className={styles['search__separator']} />
      </>
    );
  };

  const getFilteredValues = () => {
    const normalizedSearchText = searchText.toLowerCase();

    if (!searchText) {
      return options;
    }

    return options.filter((option) => {
      if (option.searchByText) {
        return option.searchByText.toLowerCase().includes(normalizedSearchText);
      }

      const optionLabel = option[optionLabelKey];
      if (typeof optionLabel !== 'string') {
        return true;
      }

      return (optionLabel as string).toLowerCase().includes(normalizedSearchText);
    });
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

    const rendeSelectAllOption = () => {
      if (!props.isMultiple || !selectAllLabel) {
        return null;
      }

      const handleSelectAll = () => {
        if (!isSelectAll) {
          setIsSelectAll(true);
          props.onChange(options.map((option) => option[optionIdKey]));
        } else {
          setIsSelectAll(false);
          resetFilter();
        }
      };

      return (
        <DropdownItem
          className={classnames('dropdown-item-sm', styles['value-item'], styles['value-item__select-all'])}
          onClick={handleSelectAll}
          toggle={false}
        >
          <span>{selectAllLabel}</span>
        </DropdownItem>
      );
    };

    return (
      <>
        {props.selectedOption && renderResetOption()}
        {rendeSelectAllOption()}
        {foundValues.map((option) => {
          const label = (
            <div className={styles['dropdown-item-content']}>
              <div className={styles['dropdown-item-content__text']}>{option[optionLabelKey]}</div>

              {typeof option.count !== 'undefined' && (
                <span className={styles['dropdown-item-content__count']}>{option.count}</span>
              )}
            </div>
          );

          return (
            <DropdownItem
              key={option[optionIdKey]}
              className={classnames('dropdown-item-sm', styles['value-item'])}
              onClick={handleChange(option)}
              toggle={!props.isMultiple}
            >
              {props.isMultiple ? (
                <Checkbox
                  checked={props.selectedOptions.includes(option[optionIdKey])}
                  title={label}
                  onClick={(e) => e.stopPropagation()}
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
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleChangeSearchText = (e: React.ChangeEvent<HTMLInputElement>) => {
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
        className={classnames('dropdown-menu-right dropdown', styles['container'], containerClassname)}
        toggle={handleToggleDropdown}
        isOpen={isDropdownOpen}
        onClick={(event) => event.stopPropagation()}
      >
        <DropdownToggle
          tag="button"
          className={classnames(
            styles['active-value'],
            toggleClassName,
            isClearHovered && styles['active-value_clear-hovered'],
          )}
        >
          {Icon && <Icon className={styles['icon']} />}
          <span className={styles['active-value__text']}>{props.renderPlaceholder(options)}</span>
          {props.isMultiple && isArrayWithItems(props.selectedOptions) ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                resetFilter();
              }}
              type="button"
              className={classnames(styles['clear-button'], arrowClassName)}
              onMouseEnter={() => setClearHovered(true)}
              onMouseLeave={() => setClearHovered(false)}
            >
              <ClearIcon />
            </button>
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

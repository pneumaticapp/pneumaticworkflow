/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count
import * as React from 'react';
// tslint:disable-next-line: no-duplicate-imports
import { useCallback, useMemo, useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import * as classnames from 'classnames';

import { Checkbox, InputField, Loader, RadioButton, TCheckboxTriState } from '..';
import { isArrayWithItems } from '../../../utils/helpers';
import { MoreBoldCirlce } from '../../icons';
import { ShowMore } from '../ShowMore';

import styles from './Filter.css';

type TOptionId = number | string | null;
type TSubOption<IdKey extends string, LabelKey extends string> = TOptionBase<IdKey, LabelKey> & {
  count?: number;
};

export type TOptionBase<IdKey extends string, LabelKey extends string> = {
  [key in IdKey]: TOptionId;
} & {
  [key in LabelKey]: string | React.ReactNode;
} & {
  customClickHandler?(): void;
  areSubOptionsLoading?: boolean;
  subOptions?: TSubOption<IdKey, LabelKey>[];
  count?: number;
};

interface IFilterCommonProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> {
  title: string;
  optionsTitle?: string;
  isInitiallyExpanded?: boolean;
  options: TOption[];
  isLoading?: boolean;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  containerClassName?: string;
  withSearch?: boolean;
  selectedSubOptions?: TOptionId[];
  renderOptionTitle?(option: TOption): React.ReactNode;
  onCheckOption?(option: TOption, callback?: () => void): void;
  onUncheckOption?(option: TOption, callback?: () => void): void;
  onCheckSubOption?(optionId: TOptionId, subOptionId: TOptionId): void;
  onUncheckSubOption?(optionId: TOptionId, subOptionId: TOptionId): void;
  onExpandOption?(option: TOption): void;
}

interface IFilterMultiOptionsProps {
  isMultiple: true;
  selectedOption?: never;
  selectedOptions: TOptionId[];
  changeFilter(optionIds: TOptionId[]): void;
}

interface IFilterSingleOptionsProps {
  isMultiple?: false;
  selectedOption: TOptionId;
  selectedOptions?: never;
  changeFilter(optionId: TOptionId | null): void;
}

export type TFilterProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> = IFilterCommonProps<IdKey, LabelKey, TOption> & (IFilterMultiOptionsProps | IFilterSingleOptionsProps);

const MAX_OPTIONS_AMOUNT = 14;

export function Filter<IdKey extends string, LabelKey extends string, TOption extends TOptionBase<IdKey, LabelKey>>(
  props: TFilterProps<IdKey, LabelKey, TOption>,
) {
  const { formatMessage } = useIntl();

  const {
    options,
    isLoading = false,
    isInitiallyExpanded = false,
    optionLabelKey,
    optionIdKey,
    title,
    containerClassName,
    withSearch,
    optionsTitle = formatMessage({ id: 'filter.default-options-title' }),
    selectedOptions,
    selectedSubOptions,
    renderOptionTitle,
    onCheckOption,
    onUncheckOption,
    onCheckSubOption,
    onUncheckSubOption,
    onExpandOption,
  } = props;

  useEffect(() => {
    selectedOptions?.forEach((optionId) => {
      const option = options.find((option) => optionId === option[optionIdKey]);
      if (option) {
        onCheckOption?.(option, () => setExpandedOptions((prev) => [...prev, option[optionIdKey]]));
      }
    });
  }, [options.length]);

  const [searchText, setSearchText] = useState('');
  const [areAllOptionsShown, setAllOptionsShown] = useState(false);
  const [expandedOptions, setExpandedOptions] = useState<TOptionId[]>([]);

  const toggleShowAll = useCallback(() => setAllOptionsShown(!areAllOptionsShown), [areAllOptionsShown]);
  const toggleExpandOption = (targetOptionId: TOptionId) => {
    const isOptionExpanded = expandedOptions.some((optionId) => targetOptionId === optionId);

    const newExpandedOptions = isOptionExpanded
      ? expandedOptions.filter((optionId) => targetOptionId !== optionId)
      : [...expandedOptions, targetOptionId];

    setExpandedOptions(newExpandedOptions);
  };

  const hasSelectedOption = useMemo(() => {
    return (
      (typeof props.selectedOption !== 'undefined' && props.selectedOption !== null) ||
      isArrayWithItems(props.selectedOptions)
    );
  }, []);

  const filteredOptions = useMemo(() => {
    if (!searchText) {
      return options;
    }

    const checkOption = (option: TOption) => {
      return (option[optionLabelKey] as string).toLowerCase().includes(searchText.toLowerCase());
    };

    return options.filter(checkOption);
  }, [searchText, options]);

  const optionsToShow = useMemo(() => {
    if (areAllOptionsShown) {
      return filteredOptions;
    }

    return filteredOptions.slice(0, MAX_OPTIONS_AMOUNT);
  }, [filteredOptions, areAllOptionsShown]);

  const hasHiddenOptions = useMemo(() => filteredOptions.length > MAX_OPTIONS_AMOUNT, [filteredOptions]);

  const handleChange = (option: TOption) => () => {
    const { customClickHandler } = option;

    if (typeof customClickHandler === 'function') {
      customClickHandler();

      return;
    }

    const optionId = option[optionIdKey];

    if (!props.isMultiple) {
      props.changeFilter(optionId);

      return;
    }

    const newIsChecked = !props.selectedOptions.includes(optionId);

    const newSelectedOptions = newIsChecked
      ? [...props.selectedOptions, optionId]
      : props.selectedOptions.filter((selectedOption) => selectedOption !== optionId);

    props.changeFilter(newSelectedOptions);

    if (newIsChecked) {
      const newExpandedOptions = [...expandedOptions, optionId];
      setExpandedOptions(newExpandedOptions);
      onCheckOption?.(option);

      return;
    }

    onUncheckOption?.(option);
  };

  const renderSubOptionsController = (option: TOption) => {
    if (!option.subOptions) {
      return null;
    }

    const isOptionExpanded = expandedOptions.some((optionId) => optionId === option[optionIdKey]);

    const onClick = () => {
      if (!isOptionExpanded) {
        onExpandOption?.(option);
      }

      toggleExpandOption(option[optionIdKey]);
    };

    return (
      <button
        className={classnames(
          styles['toggle-sub-options-btn'],
          isOptionExpanded && styles['toggle-sub-options-btn_expanded'],
        )}
        onClick={onClick}
        data-testid="show-sub-options"
        aria-label="Toggle suboptions"
      >
        <MoreBoldCirlce />
      </button>
    );
  };

  const renderSubOptions = (option: TOption) => {
    if (option.areSubOptionsLoading) {
      return <Loader isLoading isCentered={false} containerClassName={styles['sub-options-loader']} />;
    }

    const isExpanded = expandedOptions.some((optionId) => optionId === option[optionIdKey]);
    const shouldShowSubOptions = isArrayWithItems(option.subOptions) && isExpanded;

    if (!shouldShowSubOptions) {
      return null;
    }

    const onToggleSubOption =
      (optionId: TOptionId, subOptionId: TOptionId) => (event: React.ChangeEvent<HTMLInputElement>) => {
        const {
          target: { checked },
        } = event;
        const handleToggle = checked ? onCheckSubOption : onUncheckSubOption;
        handleToggle?.(optionId, subOptionId);
      };

    return (
      <div className={styles['sub-options']}>
        {option.subOptions?.map((subOption) => {
          const optionId = option[optionIdKey];
          const subOptionId = subOption[optionIdKey];

          return (
            <div className={styles['option-container']}>
              <div className={styles['option']}>
                <Checkbox
                  checked={selectedSubOptions?.includes(subOptionId)}
                  onChange={onToggleSubOption?.(optionId, subOptionId)}
                  key={subOption[optionIdKey]}
                  title={subOption[optionLabelKey]}
                  labelClassName={classnames(styles['sub-option'], styles['option__controller-label'])}
                  containerClassName={styles['option__controller']}
                  titleClassName={styles['option__controller-title']}
                />
                {typeof subOption.count === 'number' && (
                  <span className={styles['option__count']}>{subOption.count}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className={styles['loader-wrapper']}>
          <Loader isLoading />
        </div>
      );
    }

    if (!isArrayWithItems(options)) {
      return <p className={styles['placeholder']}>{formatMessage({ id: 'filter.placeholder' }, { optionsTitle })}</p>;
    }

    const OptionController = props.isMultiple ? Checkbox : RadioButton;

    const getOptionStateProp = (option: TOption) => {
      const optionId = option[optionIdKey];

      if (!props.isMultiple) {
        const checked = props.selectedOption === option[optionIdKey];

        return { checked };
      }

      if (!props.selectedOptions.includes(optionId)) {
        return { triState: 'empty' as TCheckboxTriState };
      }

      if (!option.subOptions || !selectedSubOptions || option.areSubOptionsLoading) {
        return { triState: 'checked' as TCheckboxTriState };
      }

      const allSubOptionsSelected = !option.subOptions.some(
        (subOption) => !selectedSubOptions.includes(subOption[optionIdKey]),
      );

      return {
        triState: allSubOptionsSelected ? 'checked' : ('indeterminate' as TCheckboxTriState),
      };
    };

    return (
      <>
        {withSearch && (
          <InputField
            containerClassName={styles['search-field']}
            className={styles['search-field__input']}
            placeholder={formatMessage({ id: 'filter.search' }, { optionsTitle })}
            value={searchText}
            onChange={(e) => setSearchText(e.currentTarget.value)}
            fieldSize="md"
            data-testid="search-input"
            onClear={() => setSearchText('')}
          />
        )}
        <div role="list" className={styles['options']}>
          {optionsToShow.map((option) => (
            <div className={styles['option-container']}>
              <div className={styles['option']}>
                <OptionController
                  key={option[optionIdKey]}
                  title={renderOptionTitle?.(option) || option[optionLabelKey]}
                  onChange={handleChange(option)}
                  data-testid="option"
                  containerClassName={styles['option__controller']}
                  labelClassName={styles['option__controller-label']}
                  titleClassName={styles['option__controller-title']}
                  {...getOptionStateProp(option)}
                />
                {renderSubOptionsController(option)}
              </div>
              {renderSubOptions(option)}
            </div>
          ))}
        </div>
        {hasHiddenOptions && (
          <button type="button" className={styles['show-more__toggle']} onClick={toggleShowAll}>
            {areAllOptionsShown
              ? formatMessage({ id: 'filter.show-less' }, { optionsTitle })
              : formatMessage({ id: 'filter.show-more' }, { optionsTitle })}
          </button>
        )}
      </>
    );
  };

  return (
    <ShowMore
      label={title}
      containerClassName={containerClassName}
      isInitiallyVisible={isInitiallyExpanded || hasSelectedOption}
    >
      {renderContent()}
    </ShowMore>
  );
}

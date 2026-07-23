import * as React from 'react';
import { useEffect, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { RadioButton } from '../UI/Fields/RadioButton';
import { EHighlightsDateFilter, THighlightsDateFilter } from '../../types/highlights';
import { ShowMore } from '../UI/ShowMore';
import { DatePickerCustom } from '../UI/form/DatePicker';
import { formatDatePickerDisplayValue } from '../UI/form/DatePicker/utils/normalizeDatePickerDate';
import { useDatePickerSettings } from '../../hooks/useDatePickerSettings';

import styles from './Filters.css';

export interface IDateFilterProps {
  endDate: Date | null;
  selectedDateFilter: THighlightsDateFilter;
  startDate: Date | null;
  changeEndDate(date: Date): void;
  changeSelectedDateFilter(filter: EHighlightsDateFilter): () => void;
  changeStartDate(date: Date): void;
  /**
   * Reports whether Custom range draft is complete (both ends set),
   * or true for non-Custom presets. Used to disable Apply while editing.
   */
  onCustomRangeValidityChange?(isComplete: boolean): void;
}

export function DateFilter({
  startDate,
  endDate,
  selectedDateFilter,
  changeSelectedDateFilter,
  changeEndDate,
  changeStartDate,
  onCustomRangeValidityChange,
}: IDateFilterProps) {
  const { formatMessage } = useIntl();
  const { timezone } = useDatePickerSettings();

  const startDatePlaceholder = formatMessage({ id: 'process-highlights.date-picker-start-date' });
  const endDatePlaceholder = formatMessage({ id: 'process-highlights.date-picker-end-date' });
  const rangePlaceholder = `${startDatePlaceholder} — ${endDatePlaceholder}`;
  const isCustomSelected = selectedDateFilter === EHighlightsDateFilter.Custom;

  // Draft range so a first click [start, null] can clear end without keeping a stale Redux endDate.
  const [draftStartDate, setDraftStartDate] = useState<Date | null>(startDate);
  const [draftEndDate, setDraftEndDate] = useState<Date | null>(endDate);

  useEffect(() => {
    setDraftStartDate(startDate);
    setDraftEndDate(endDate);
  }, [startDate, endDate, selectedDateFilter]);

  useEffect(() => {
    if (!onCustomRangeValidityChange) {
      return;
    }

    const isComplete = !isCustomSelected || Boolean(draftStartDate && draftEndDate);

    onCustomRangeValidityChange(isComplete);
  }, [draftStartDate, draftEndDate, isCustomSelected, onCustomRangeValidityChange]);

  const DATE_FILTER_OPTIONS = [
    {
      id: 'date-picker-today',
      label: formatMessage({ id: 'process-highlights.date-picker-today' }),
      type: EHighlightsDateFilter.Today,
    },
    {
      id: 'date-picker-yesterday',
      label: formatMessage({ id: 'process-highlights.date-picker-yesterday' }),
      type: EHighlightsDateFilter.Yesterday,
    },
    {
      id: 'date-picker-week',
      label: formatMessage({ id: 'process-highlights.date-picker-week' }),
      type: EHighlightsDateFilter.Week,
    },
    {
      id: 'date-picker-month',
      label: formatMessage({ id: 'process-highlights.date-picker-month' }),
      type: EHighlightsDateFilter.Month,
    },
    {
      id: 'date-picker-custom',
      label: formatMessage({ id: 'process-highlights.date-picker-custom' }),
      type: EHighlightsDateFilter.Custom,
    },
  ];

  const handleChangeRange = ([nextStartDate, nextEndDate]: [Date | null, Date | null]) => {
    setDraftStartDate(nextStartDate);
    setDraftEndDate(nextEndDate);

    if (nextStartDate && nextEndDate) {
      changeStartDate(nextStartDate);
      changeEndDate(nextEndDate);
    }
  };

  const startText = draftStartDate ? formatDatePickerDisplayValue(draftStartDate, timezone) : '';
  const endText = draftEndDate ? formatDatePickerDisplayValue(draftEndDate, timezone) : '';

  return (
    <ShowMore
      containerClassName={styles['filter']}
      label="process-highlights.date-picker-by-time-label"
      isInitiallyVisible
    >
      <div className={styles['filter__options']}>
        {DATE_FILTER_OPTIONS.map(({ id, label, type }) => (
          <RadioButton
            checked={type === selectedDateFilter}
            key={id}
            title={label}
            onChange={changeSelectedDateFilter(type)}
            id={id}
          />
        ))}
      </div>
      {isCustomSelected && (
        <div className={styles['filter__datepicker']}>
          <div className={styles['filter__datepicker-display']} aria-hidden>
            <span
              className={classnames(
                styles['filter__datepicker-start'],
                !startText && styles['filter__datepicker-placeholder'],
              )}
            >
              {startText || startDatePlaceholder}
            </span>
            <span className={styles['filter__datepicker-separator']}>—</span>
            <span
              className={classnames(
                styles['filter__datepicker-end'],
                !endText && styles['filter__datepicker-placeholder'],
              )}
            >
              {endText || endDatePlaceholder}
            </span>
          </div>
          <DatePickerCustom
            className={styles['filter__datepicker-input']}
            endDate={draftEndDate}
            isClearable={false}
            onChange={handleChangeRange}
            placeholderText={rangePlaceholder}
            selectsRange
            startDate={draftStartDate}
            wrapperClassName={styles['filter__datepicker-wrapper']}
          />
        </div>
      )}
    </ShowMore>
  );
}

import * as React from 'react';
import { useEffect, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { RadioButton } from '../UI/Fields/RadioButton';
import { EHighlightsDateFilter, THighlightsDateFilter } from '../../types/highlights';
import { ShowMore } from '../UI/ShowMore';
import { DatePickerCustom } from '../UI/form/DatePicker';

import styles from './Filters.css';

export interface IDateFilterProps {
  endDate: Date | null;
  selectedDateFilter: THighlightsDateFilter;
  startDate: Date | null;
  changeEndDate(date: Date): void;
  changeSelectedDateFilter(filter: EHighlightsDateFilter): () => void;
  changeStartDate(date: Date): void;
}

export function DateFilter({
  startDate,
  endDate,
  selectedDateFilter,
  changeSelectedDateFilter,
  changeEndDate,
  changeStartDate,
}: IDateFilterProps) {
  const { formatMessage } = useIntl();

  const startDatePlaceholder = formatMessage({ id: 'process-highlights.date-picker-start-date' });
  const endDatePlaceholder = formatMessage({ id: 'process-highlights.date-picker-end-date' });
  const rangePlaceholder = `${startDatePlaceholder} — ${endDatePlaceholder}`;

  const lastCheckboxClassName = selectedDateFilter === EHighlightsDateFilter.Custom ? styles['mb-2'] : styles['mb-4'];

  // Draft range so a first click [start, null] can clear end without keeping a stale Redux endDate.
  const [draftStartDate, setDraftStartDate] = useState<Date | null>(startDate);
  const [draftEndDate, setDraftEndDate] = useState<Date | null>(endDate);

  useEffect(() => {
    setDraftStartDate(startDate);
    setDraftEndDate(endDate);
  }, [startDate, endDate, selectedDateFilter]);

  const DATE_FILTER_CHECKBOXES = [
    {
      containerClassName: styles['mb-1'],
      id: 'date-picker-today',
      label: formatMessage({ id: 'process-highlights.date-picker-today' }),
      type: EHighlightsDateFilter.Today,
    },
    {
      containerClassName: styles['mb-1'],
      id: 'date-picker-yesterday',
      label: formatMessage({ id: 'process-highlights.date-picker-yesterday' }),
      type: EHighlightsDateFilter.Yesterday,
    },
    {
      containerClassName: styles['mb-1'],
      id: 'date-picker-week',
      label: formatMessage({ id: 'process-highlights.date-picker-week' }),
      type: EHighlightsDateFilter.Week,
    },
    {
      containerClassName: styles['mb-1'],
      id: 'date-picker-month',
      label: formatMessage({ id: 'process-highlights.date-picker-month' }),
      type: EHighlightsDateFilter.Month,
    },
    {
      containerClassName: styles['mb-1'],
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

  return (
    <ShowMore
      containerClassName={styles['filter-container']}
      label="process-highlights.date-picker-by-time-label"
      isInitiallyVisible
    >
      {DATE_FILTER_CHECKBOXES.map(({ containerClassName, id, label, type }, idx) => (
        <RadioButton
          checked={type === selectedDateFilter}
          containerClassName={idx === DATE_FILTER_CHECKBOXES.length - 1 ? lastCheckboxClassName : containerClassName}
          key={id}
          title={label}
          onChange={changeSelectedDateFilter(type)}
          id={id}
        />
      ))}
      {selectedDateFilter === EHighlightsDateFilter.Custom && (
        <div
          className={classnames(
            styles['date-filter-custom'],
            selectedDateFilter === EHighlightsDateFilter.Custom && styles['mb-4'],
          )}
        >
          <DatePickerCustom
            className={styles['datepicker__input']}
            endDate={draftEndDate}
            onChange={handleChangeRange}
            placeholderText={rangePlaceholder}
            selectsRange
            startDate={draftStartDate}
            wrapperClassName={styles['datepicker']}
          />
        </div>
      )}
    </ShowMore>
  );
}

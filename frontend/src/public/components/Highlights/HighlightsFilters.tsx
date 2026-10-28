import React, { ChangeEvent, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { EPageTitle } from '../../constants/defaultValues';
import { useDatePickerSettings } from '../../hooks/useDatePickerSettings';
import { loadHighlights, setHighlightsFilters, setHighlightsFiltersChanged } from '../../redux/highlights/slice';
import { getInitHighlightsFilters } from '../../redux/highlights/utils/getInitHighlightsFilters';
import { getAccountsUsers } from '../../redux/selectors/accounts';
import {
  getHighlightsFilters,
  getHighlightsIsTemplatesTitlesLoading,
  getHighlightsTemplatesTitles,
} from '../../redux/selectors/highlights';
import { EHighlightsDateFilter, EHighlightsFilterType } from '../../types/highlights';
import { getActiveUsers } from '../../utils/users';
import { PageTitle } from '../PageTitle/PageTitle';
import { Button } from '../UI';
import { DateFilter } from './DateFilter';
import { TemplatesFilter } from './TemplatesFilter';
import { UsersFilter } from './UsersFilter';
import { getHighlightsDateRange } from './utils/highlightsDateRange';

import styles from './HighlightsFeed.css';

export function HighlightsFilters() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const { timezone, dateFdw } = useDatePickerSettings();
  const { timeRange, startDate, endDate, usersFilter, templatesFilter } = useSelector(getHighlightsFilters);
  const templatesTitles = useSelector(getHighlightsTemplatesTitles);
  const isTemplatesTitlesLoading = useSelector(getHighlightsIsTemplatesTitlesLoading);
  const users = getActiveUsers(useSelector(getAccountsUsers));

  const [templatesSearchText, setTemplatesSearchText] = useState('');
  const [usersSearchText, setUsersSearchText] = useState('');
  const [isDateFilterReady, setIsDateFilterReady] = useState(true);

  const handleChangeTemplatesSearchText = (e: ChangeEvent<HTMLInputElement>) => {
    setTemplatesSearchText(e.target.value);
  };

  const handleChangeUsersSearchText = (e: ChangeEvent<HTMLInputElement>) => {
    setUsersSearchText(e.target.value);
  };

  const handleChangeFilterList =
    (type: EHighlightsFilterType) =>
    (id: number) =>
    ({ target: { checked } }: ChangeEvent<HTMLInputElement>) => {
      const filterKey = type === EHighlightsFilterType.Templates ? 'templatesFilter' : 'usersFilter';
      const filterList = type === EHighlightsFilterType.Templates ? templatesFilter : usersFilter;
      const isSelected = filterList.includes(id);

      if (checked && !isSelected) {
        dispatch(setHighlightsFilters({ [filterKey]: [...filterList, id] }));
      }

      if (!checked && isSelected) {
        dispatch(setHighlightsFilters({ [filterKey]: filterList.filter((filterId) => filterId !== id) }));
      }
    };

  const handleChangeSelectedDateFilter = (selectedTimeRange: EHighlightsDateFilter) => () => {
    if (selectedTimeRange === timeRange) {
      return;
    }

    const newRange = getHighlightsDateRange(selectedTimeRange, timezone, dateFdw);

    dispatch(setHighlightsFilters({ timeRange: selectedTimeRange, ...newRange }));
  };

  const handleChangeStartDate = (newStartDate: Date) => {
    dispatch(setHighlightsFilters({ startDate: newStartDate }));
  };

  const handleChangeEndDate = (newEndDate: Date) => {
    dispatch(setHighlightsFilters({ endDate: newEndDate }));
  };

  const handleApplyFilters = () => {
    dispatch(loadHighlights({}));
    dispatch(setHighlightsFiltersChanged());
  };

  const handleClearFilters = () => {
    const initFilters = getInitHighlightsFilters();

    dispatch(
      setHighlightsFilters({ ...initFilters, ...getHighlightsDateRange(initFilters.timeRange, timezone, dateFdw) }),
    );
    dispatch(loadHighlights({}));
  };

  return (
    <div className={styles['filters']}>
      <PageTitle titleId={EPageTitle.Highlights} />
      <DateFilter
        endDate={endDate}
        startDate={startDate}
        selectedDateFilter={timeRange}
        changeSelectedDateFilter={handleChangeSelectedDateFilter}
        changeEndDate={handleChangeEndDate}
        changeStartDate={handleChangeStartDate}
        onCustomRangeValidityChange={setIsDateFilterReady}
      />
      <TemplatesFilter
        changeTemplatesSearchText={handleChangeTemplatesSearchText}
        changeTemplatesFilter={handleChangeFilterList(EHighlightsFilterType.Templates)}
        searchText={templatesSearchText}
        selectedTemplates={templatesFilter}
        templatesTitles={templatesTitles}
        isFiltersLoading={isTemplatesTitlesLoading}
      />
      <UsersFilter
        changeUsersFilter={handleChangeFilterList(EHighlightsFilterType.Users)}
        changeUsersSearchText={handleChangeUsersSearchText}
        searchText={usersSearchText}
        selectedUsers={usersFilter}
        users={users}
      />
      <div className={styles['filters__buttons']}>
        <div className={styles['button_save-container']}>
          <Button
            disabled={!isDateFilterReady}
            onClick={handleApplyFilters}
            type="button"
            label={formatMessage({ id: 'workflow-highlights.button-apply-filters' })}
            size="md"
          />
        </div>
        <div className={styles['button_clear-container']}>
          <Button
            className="cancel-button"
            onClick={handleClearFilters}
            label={formatMessage({ id: 'process-highlights.button-clear' })}
          />
        </div>
      </div>
    </div>
  );
}

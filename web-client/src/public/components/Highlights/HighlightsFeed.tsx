/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:max-file-line-count */
import classnames from 'classnames';
import * as React from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';

import { ERoutes } from '../../constants/routes';
import {
  EHighlightsDateFilter,
  EHighlightsFilterType,
  IHighlightsItem,
} from '../../types/highlights';
import { TITLES } from '../../constants/titles';
import { history } from '../../utils/history';
import { PROCESS_HIGHLIGHTS_DATE_RANGE_MAP } from '../../utils/dateTime';
import { UsersFilter } from './UsersFilter';
import { IGetTemplatesTitlesRequesConfig } from '../../api/getTemplatesTitles';
import { ILoadHighlightsConfig } from '../../redux/highlights/actions';
import { IHighlightsFilters } from '../../types/redux';
import { INIT_FILTERS } from '../../redux/highlights/reducer';
import { isArrayWithItems } from '../../utils/helpers';
import { TUserListItem } from '../../types/user';
import { ITemplateTitle } from '../../types/template';
import { Placeholder, Button } from '../UI';
import { TOpenWorkflowLogPopupPayload } from '../../redux/actions';

import { HighlightsPlaceholderIcon } from './HighlightsPlaceholderIcon';
import { TemplatesFilter } from './TemplatesFilter';
import { DateFilter } from './DateFilter';
import { FeedItem } from './FeedItem';
import styles from './HighlightsFeed.css';
import { EPageTitle } from '../../constants/defaultValues';
import { PageTitle } from '../PageTitle/PageTitle';

export interface IHighlightsFeedProps {
  count: number;
  isFeedLoading: boolean;
  isWorkflowLogPopupLoading?: boolean;
  isTemplatesTitlesLoading: boolean;
  items: IHighlightsItem[];
  workflowId: number | null;
  users: TUserListItem[];
  templatesTitles: ITemplateTitle[];
  timeRange: EHighlightsDateFilter;
  startDate: Date;
  endDate: Date;
  usersFilter: number[];
  templatesFilter: number[];
  filtersChanged: boolean;
  loadHighlights({ limit, offset, onScroll }: ILoadHighlightsConfig): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
  resetHightlightsStore(): void;
  loadTemplatesTitles({ eventDateFrom, eventDateTo }: IGetTemplatesTitlesRequesConfig): void;
  setFilters(value: Partial<IHighlightsFilters>): void;
  setFiltersChanged(): void;
}

export function HighlightsFeed({
  count,
  isWorkflowLogPopupLoading,
  items,
  workflowId,
  isFeedLoading,
  templatesTitles,
  users,
  isTemplatesTitlesLoading,
  timeRange,
  startDate,
  endDate,
  usersFilter,
  templatesFilter,
  filtersChanged,
  setFilters,
  loadHighlights,
  openWorkflowLogPopup,
  resetHightlightsStore,
  loadTemplatesTitles,
  setFiltersChanged,
}: IHighlightsFeedProps) {
  const { useCallback, useEffect, useMemo, useState } = React;
  const { formatMessage } = useIntl();

  const [isFirstFetch, setIsFirstFetch] = useState(true);

  useEffect(() => {
    document.title = TITLES.WorkflowHighlights;

    loadHighlights({ onScroll: true });
    setIsFirstFetch(false);

    return () => {
      resetHightlightsStore();
    };
  }, []);

  useEffect(() => {
    loadTemplatesTitles({ eventDateFrom: startDate, eventDateTo: endDate });
  }, [endDate, startDate]);

  const [templatesSearchText, setTemplatesSearchText] = useState('');
  const handleChangeTemplatesSearchText = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTemplatesSearchText(e.target.value);
  };

  const [usersSearchText, setUsersSearchText] = useState('');
  const handleChangeUsersSearchText = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUsersSearchText(e.target.value);
  };

  const isListFullyFetched = useMemo(
    () => items.length === count && !isFirstFetch,
    [count, items, isFirstFetch],
  );

  const isFeedEmpty = useMemo(
    () => !isArrayWithItems(items) && !isFirstFetch,
    [items, isFirstFetch],
  );

  const handleChangeFilterList = (type: EHighlightsFilterType) => (id: number) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const { target: { checked } } = e;

      const filterListMap = {
        [EHighlightsFilterType.Templates]: {
          filterList: templatesFilter,
          setFilterList: (value: number[]) => setFilters({ templatesFilter: value }),
        },
        [EHighlightsFilterType.Users]: {
          filterList: usersFilter,
          setFilterList: (value: number[]) => setFilters({ usersFilter: value }),
        },
      };

      const { filterList, setFilterList } = filterListMap[type];

      const isSelected = filterList.includes(id);
      const shouldAdd = checked && !isSelected;
      const shouldDelete = !checked && isSelected;

      if (shouldAdd) {
        setFilterList([...filterList, id]);
      }

      if (shouldDelete) {
        setFilterList([...filterList.filter(x => x !== id)]);
      }
    };

  const handleInstantlyChangeFilterList = (type: EHighlightsFilterType) => (id?: number) => () => {
    if (!id) {
      return;
    }

    const filterList = type === EHighlightsFilterType.Templates
      ? templatesFilter
      : usersFilter;
    const setFilterList = type === EHighlightsFilterType.Templates
      ? (value: number[]) => setFilters({ templatesFilter: value })
      : (value: number[]) => setFilters({ usersFilter: value });
    const isSelected = filterList.includes(id);

    if (isSelected) {
      return;
    }

    const newFilterList = [...filterList, id];
    setFilterList(newFilterList);

    loadHighlights({});
  };

  const handleChangeSelectedDateFilter = useCallback((selectedTimeRange: EHighlightsDateFilter) => () => {
    if (selectedTimeRange === timeRange) {
      return;
    }

    setFilters({ timeRange: selectedTimeRange });

    if (selectedTimeRange !== EHighlightsDateFilter.Custom) {
      const { startDate, endDate } = PROCESS_HIGHLIGHTS_DATE_RANGE_MAP[selectedTimeRange];

      setFilters({ startDate, endDate });
    }
  }, [timeRange]);

  const handleApplyFilters = () => {
    loadHighlights({});
    setFiltersChanged();
  };

  const handleClearFilters = () => {
    setFilters(INIT_FILTERS);

    loadHighlights({});
  };

  const onScroll = () => {
    if (!isFeedLoading) {
      loadHighlights({ offset: items.length, onScroll: true });
    }
  };

  const [workflowLogWorkflowId, setWorkflowLogWorkflowId] = useState<number | null>(null);
  const handleOpenWorkflowLogPopup = useCallback((workflowId: number) => () => {
    setWorkflowLogWorkflowId(workflowId);
    openWorkflowLogPopup({ workflowId });
  },
  [workflowLogWorkflowId],
  );

  const handleRedirectToTemplate = (templateId?: number) => () => {
    if (!templateId) {
      return;
    }

    const redirectUrl = ERoutes.TemplatesEdit.replace(':id', String(templateId));
    history.replace(redirectUrl);
  };
  const containerClassName = classnames(
    'container',
    styles['process-highlights-feed__container'],
    isWorkflowLogPopupLoading && styles['process-highlights-feed__container_disabled'],
  );

  const renderPlaceholder = () => {
    if (!isFeedEmpty || isFeedLoading) {
      return null;
    }

    if (filtersChanged) {
      return (
        <Placeholder
          mood="bad"
          Icon={HighlightsPlaceholderIcon}
          title={formatMessage({ id: 'workflow-highlights.placeholder-empty-search-title' })}
          description={formatMessage({ id: 'workflow-highlights.placeholder-empty-search-descrtiption' })}
        />
      );
    }

    return (
      <Placeholder
        mood="neutral"
        Icon={HighlightsPlaceholderIcon}
        title={formatMessage({ id: 'workflow-highlights.placeholder-empty-list-title' })}
        description={formatMessage({ id: 'workflow-highlights.placeholder-empty-list-descrtiption' })}
      />
    );
  };

  return (
    <div className={containerClassName}>
      <div className="row">
        <div className="col-md-4 mb-5 mb-md-0">
          <div className={styles['filters']}>
            <PageTitle titleId={EPageTitle.Highlights} />
            <DateFilter
              endDate={endDate}
              startDate={startDate}
              selectedDateFilter={timeRange}
              changeSelectedDateFilter={handleChangeSelectedDateFilter}
              changeEndDate={(endDate: Date) => setFilters({ endDate })}
              changeStartDate={(startDate: Date) => setFilters({ startDate })}
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
        </div>
        <div className="col-md-8 h-100">
          <div className={styles['feed']}>
            <InfiniteScroll
              hasMore={isFeedLoading || !isListFullyFetched}
              next={onScroll}
              dataLength={items.length}
              loader={<div className={classnames('loading', styles['feed__spinner'])} />}
            >
              {items.map(item => (
                <FeedItem
                  {...item}
                  item={item}
                  redirectToTemplate={handleRedirectToTemplate}
                  applyTemplatesFilter={handleInstantlyChangeFilterList(EHighlightsFilterType.Templates)}
                  applyUserFilter={handleInstantlyChangeFilterList(EHighlightsFilterType.Users)}
                  key={`FeedItem${item.id}`}
                  openProcessLogPopup={handleOpenWorkflowLogPopup(item.workflow.id)}
                  isProcessLogPopupLoading={isWorkflowLogPopupLoading && item.workflow.id === workflowId}
                />
              ))}
            </InfiniteScroll>
            {renderPlaceholder()}
          </div>
        </div>
      </div>
    </div>
  );
}

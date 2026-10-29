import classnames from 'classnames';
import React from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useDispatch, useSelector } from 'react-redux';

import { ERoutes } from '../../constants/routes';
import { loadHighlights, setHighlightsFilters } from '../../redux/highlights/slice';
import {
  getHighlightsCount,
  getHighlightsFilters,
  getHighlightsIsFeedLoading,
  getHighlightsItems,
} from '../../redux/selectors/highlights';
import { getWorkflowLogIsLoading, getWorkflowLogWorkflowId } from '../../redux/selectors/workflowLog';
import { openWorkflowLogPopup } from '../../redux/workflows/slice';
import { EHighlightsFilterType } from '../../types/highlights';
import { isArrayWithItems } from '../../utils/helpers';
import { history } from '../../utils/history';
import { FeedItem } from './FeedItem';
import { HighlightsPlaceholder } from './HighlightsPlaceholder';
import { IHighlightsListProps } from './types';

import styles from './HighlightsFeed.css';

export function HighlightsList({ isFirstFetch }: IHighlightsListProps) {
  const dispatch = useDispatch();
  const count = useSelector(getHighlightsCount);
  const items = useSelector(getHighlightsItems);
  const isFeedLoading = useSelector(getHighlightsIsFeedLoading);
  const { usersFilter, templatesFilter, hasChangedFilters } = useSelector(getHighlightsFilters);
  const isWorkflowLogPopupLoading = useSelector(getWorkflowLogIsLoading);
  const workflowLogWorkflowId = useSelector(getWorkflowLogWorkflowId);

  const isListFullyFetched = items.length === count && !isFirstFetch;
  const isFeedEmpty = !isArrayWithItems(items) && !isFirstFetch;

  const handleApplyFilter = (type: EHighlightsFilterType) => (id?: number) => () => {
    const filterKey = type === EHighlightsFilterType.Templates ? 'templatesFilter' : 'usersFilter';
    const filterList = type === EHighlightsFilterType.Templates ? templatesFilter : usersFilter;

    if (!id || filterList.includes(id)) {
      return;
    }

    dispatch(setHighlightsFilters({ [filterKey]: [...filterList, id] }));
    dispatch(loadHighlights({}));
  };

  const handleOpenWorkflowLogPopup = (workflowId: number) => () => {
    dispatch(openWorkflowLogPopup({ workflowId }));
  };

  const handleRedirectToTemplate = (templateId?: number) => () => {
    if (!templateId) {
      return;
    }

    history.replace(ERoutes.TemplatesEdit.replace(':id', String(templateId)));
  };

  const handleScroll = () => {
    if (!isFeedLoading) {
      dispatch(loadHighlights({ offset: items.length, onScroll: true }));
    }
  };

  return (
    <div className={styles['feed']}>
      <InfiniteScroll
        hasMore={isFeedLoading || !isListFullyFetched}
        next={handleScroll}
        dataLength={items.length}
        loader={<div className={classnames('loading', styles['feed__spinner'])} />}
        scrollableTarget="app-container"
      >
        {items.map((item) => (
          <FeedItem
            {...item}
            item={item}
            redirectToTemplate={handleRedirectToTemplate}
            applyTemplatesFilter={handleApplyFilter(EHighlightsFilterType.Templates)}
            applyUserFilter={handleApplyFilter(EHighlightsFilterType.Users)}
            key={`FeedItem${item.id}`}
            openProcessLogPopup={handleOpenWorkflowLogPopup(item.workflow.id)}
            isProcessLogPopupLoading={isWorkflowLogPopupLoading && item.workflow.id === workflowLogWorkflowId}
          />
        ))}
      </InfiniteScroll>
      {isFeedEmpty && !isFeedLoading && <HighlightsPlaceholder hasChangedFilters={hasChangedFilters} />}
    </div>
  );
}

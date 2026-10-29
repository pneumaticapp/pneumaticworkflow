import classnames from 'classnames';
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { TITLES } from '../../constants/titles';
import { useDatePickerSettings } from '../../hooks/useDatePickerSettings';
import {
  loadHighlights,
  loadHighlightsTemplatesTitles,
  resetHighlightsStore,
  setHighlightsFilters,
} from '../../redux/highlights/slice';
import { getHighlightsFilters } from '../../redux/selectors/highlights';
import { getWorkflowLogIsLoading } from '../../redux/selectors/workflowLog';
import { getHighlightsDateRange } from './utils/highlightsDateRange';
import { HighlightsFilters } from './HighlightsFilters';
import { HighlightsList } from './HighlightsList';

import styles from './HighlightsFeed.css';

export function HighlightsFeed() {
  const dispatch = useDispatch();
  const { timeRange, startDate, endDate } = useSelector(getHighlightsFilters);
  const isWorkflowLogPopupLoading = useSelector(getWorkflowLogIsLoading);
  const { timezone, dateFdw } = useDatePickerSettings();

  const [isFirstFetch, setIsFirstFetch] = useState(true);

  useEffect(() => {
    document.title = TITLES.WorkflowHighlights;

    const currentRange = getHighlightsDateRange(timeRange, timezone, dateFdw);

    if (currentRange) {
      dispatch(setHighlightsFilters(currentRange));
    }

    dispatch(loadHighlights({ onScroll: true }));
    setIsFirstFetch(false);

    return () => {
      dispatch(resetHighlightsStore());
    };
  }, []);

  useEffect(() => {
    dispatch(loadHighlightsTemplatesTitles({ eventDateFrom: startDate, eventDateTo: endDate }));
  }, [dispatch, endDate, startDate]);

  const containerClassName = classnames(
    'container',
    styles['process-highlights-feed__container'],
    isWorkflowLogPopupLoading && styles['process-highlights-feed__container_disabled'],
  );

  return (
    <div className={containerClassName}>
      <div className="row">
        <div className="col-md-4 mb-5 mb-md-0">
          <HighlightsFilters />
        </div>
        <div className="col-md-8 h-100">
          <HighlightsList isFirstFetch={isFirstFetch} />
        </div>
      </div>
    </div>
  );
}

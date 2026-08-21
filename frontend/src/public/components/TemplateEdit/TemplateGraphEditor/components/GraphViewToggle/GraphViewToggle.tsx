import * as React from 'react';
import { useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { Tabs } from '../../../../UI';
import { EGraphViewMode, GRAPH_VIEW_TOGGLE_OPTIONS } from '../../types';
import { setViewMode } from '../../../../../redux/templateGraphView/slice';
import { selectTemplateViewMode } from '../../../../../redux/selectors/templateGraphView';
import styles from './GraphViewToggle.css';

interface IToggleTab {
  id: EGraphViewMode;
  label: string;
}

export const GraphViewToggle = () => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const viewMode = useSelector(selectTemplateViewMode);

  const handleChange = useCallback((id: IToggleTab['id']) => {
    dispatch(setViewMode(id));
  }, [dispatch]);

  const values = useMemo(
    (): IToggleTab[] =>
      GRAPH_VIEW_TOGGLE_OPTIONS.map((option) => ({
        id: option.id,
        label: formatMessage({ id: option.labelId }),
      })),
    [formatMessage],
  );

  return (
    <div
      className={styles['graph-view-toggle']}
      role="group"
      aria-label={formatMessage({ id: 'template.view-mode' })}
      data-test-id="template-view-toggle"
    >
      <Tabs<IToggleTab> activeValueId={viewMode} values={values} onChange={handleChange} />
    </div>
  );
};

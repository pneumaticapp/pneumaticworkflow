import * as React from 'react';
import { useEffect, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { IDatasetSourceToggleProps } from './types';
import { IExtraFieldSelection } from '../../../../../types/template';
import { TruncatedTooltip } from './TruncatedTooltip';
import { useCheckDevice } from '../../../../../hooks/useCheckDevice';
import { getEmptySelection } from '../../../KickoffRedux/utils/getEmptySelection';

import styles from './DatasetSourceToggle.css';

export function DatasetSourceToggle({
  field,
  editField,
  isDisabled = false,
  datasetName,
  children,
}: IDatasetSourceToggleProps) {
  const { dataset, selections } = field;
  const intl = useIntl();
  const { isMobile } = useCheckDevice();

  const [savedSelections, setSavedSelections] = useState<IExtraFieldSelection[] | null>(null);

  useEffect(() => {
    if (!dataset && selections) {
      setSavedSelections(selections as IExtraFieldSelection[]);
    }
  }, [selections, dataset]);

  const handleClearDataset = () => {
    editField({ dataset: null, selections: savedSelections || [getEmptySelection()] });
  };

  const clearButton = (
    <button
      type="button"
      className={styles['dataset-source-toggle__clear-btn']}
      onClick={handleClearDataset}
    >
      {intl.formatMessage({ id: 'template.field-dataset-clear' })}
    </button>
  );

  const content = dataset ? (
    <div className={styles['dataset-source-toggle__content']}>
      <div className={styles['dataset-source-toggle__info']}>
        <div className={styles['dataset-source-toggle__info-dataset']}>
          <span className={styles['dataset-source-toggle__info-label']}>
            {intl.formatMessage({ id: 'template.datasets' })}:
          </span>
          <TruncatedTooltip
            label={datasetName}
            containerClassName={styles['dataset-source-toggle__info-tag-tooltip']}
            {...(isMobile ? { trigger: 'click' } : {})}
          >
            <span className={classnames(styles['dataset-source-toggle__info-tag'], styles['dataset-source-toggle__option-text'])}>
              {datasetName}
            </span>
          </TruncatedTooltip>
        </div>
        {!isDisabled && clearButton}
      </div>
    </div>
  ) : (
    <div className={styles['dataset-source-toggle__content']}>
      {children}
    </div>
  );

  return (
    <div className={styles['dataset-source-toggle']}>
      {content}
    </div>
  );
}

import * as React from 'react';
import { useEffect, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { IOutputFieldContentProps } from './types';
import { IExtraFieldSelection } from '../../../../../types/template';
import { TruncatedTooltip } from './TruncatedTooltip';
import { useCheckDevice } from '../../../../../hooks/useCheckDevice';
import { getEmptySelection } from '../../../KickoffRedux/utils/getEmptySelection';

import styles from './OutputFieldContent.css';

export function OutputFieldContent({
  field,
  editField,
  isDisabled = false,
  datasetName,
  children,
}: IOutputFieldContentProps) {
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
      className={styles['output-field-content__clear-btn']}
      onClick={handleClearDataset}
    >
      {intl.formatMessage({ id: 'template.field-dataset-clear' })}
    </button>
  );

  const content = dataset && datasetName ? (
    <div className={styles['output-field-content__content']}>
      <div className={styles['output-field-content__info']}>
        <div className={styles['output-field-content__info-dataset']}>
          <span className={styles['output-field-content__info-label']}>
            {intl.formatMessage({ id: 'template.datasets' })}:
          </span>
          <TruncatedTooltip
            label={datasetName}
            containerClassName={styles['output-field-content__info-tag-tooltip']}
            {...(isMobile ? { trigger: 'click' } : {})}
          >
            <span className={classnames(styles['output-field-content__info-tag'], styles['output-field-content__option-text'])}>
              {datasetName}
            </span>
          </TruncatedTooltip>
        </div>
        {!isDisabled && clearButton}
      </div>
    </div>
  ) : (
    <div className={styles['output-field-content__content']}>
      {children}
    </div>
  );

  return (
    <div className={styles['output-field-content']}>
      {content}
    </div>
  );
}

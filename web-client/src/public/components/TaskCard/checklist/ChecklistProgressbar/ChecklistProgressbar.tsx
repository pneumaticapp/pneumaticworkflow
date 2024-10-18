import * as React from 'react';
import ReactDOM from 'react-dom';
import { useIntl } from 'react-intl';

import { createProgressbarPlaceholderId } from '../createProgressbarPlaceholderId';
import { EProgressbarColor, ProgressBar } from '../../../ProgressBar';
import { getPercent } from '../../../../utils/helpers';
import { Tooltip } from '../../../UI';
import { StarIcon } from '../../../icons';

import styles from '../../../RichText/RichText.css';

export type TChecklistProgressbarOwnProps = {
  listApiName: string;
}

export type TChecklistProgressbarReduxProps = {
  checkedItems: number;
  totalItems: number;
};

type IChecklistProgressbarProps = TChecklistProgressbarOwnProps & TChecklistProgressbarReduxProps;

export function ChecklistProgressbar({
  listApiName,
  checkedItems,
  totalItems,
}: IChecklistProgressbarProps) {
  const { formatMessage } = useIntl();

  const element = document.getElementById(createProgressbarPlaceholderId(listApiName));
  if (!element) {
    return null;
  }

  const renderProgressbar = () => {
    return (
      <div className={styles['progressbar']}>
        <ProgressBar  progress={getPercent(checkedItems, totalItems)} color={EProgressbarColor.Green} background="#fdf7ee" />

        <div className={styles['progressbar-hint']}>
          <Tooltip content={(
            <>
              {formatMessage({ id: 'task.progressbar-hint' })}

              {/* <div>
                <a target="_blank" rel="noreferrer" href={ELearnMoreLinks.Checklists}>
                  {formatMessage({ id: 'dashboard.integrations-tooltip-link' })}
                </a>
              </div> */}
            </>
          )}>
            <span className={styles['progressbar-hint-icon']}>
              <StarIcon />
            </span>
          </Tooltip>
        </div>
      </div>
    )
  }
  return ReactDOM.createPortal(
    renderProgressbar(),
    element
  );
}

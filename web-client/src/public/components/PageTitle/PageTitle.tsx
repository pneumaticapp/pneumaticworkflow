import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { Tooltip, Header, THeaderSize } from '../UI';
import { FilledInfoIcon } from '../icons';
import { ELearnMoreLinks, EPageTitle } from '../../constants/defaultValues';

import styles from './PageTitle.css';

const tooltipTextMap: { [key in EPageTitle]: string } = {
  [EPageTitle.MyTasks]: 'tasks.title.tooltip',
  [EPageTitle.Workflows]: 'workflows.title.tooltip',
  [EPageTitle.Templates]: 'templates.title.tooltip',
  [EPageTitle.TemplatesSystem]: 'templates.title-system.tooltip',
  [EPageTitle.Highlights]: 'workflow-highlights.title.tooltip',
  [EPageTitle.Integrations]: 'integrations.title.tooltip',
  [EPageTitle.Team]: 'team.title.tooltip',
};

const learnMoreLinkMap: { [key in EPageTitle]: ELearnMoreLinks } = {
  [EPageTitle.MyTasks]: ELearnMoreLinks.Tasks,
  [EPageTitle.Workflows]: ELearnMoreLinks.Workflows,
  [EPageTitle.Templates]: ELearnMoreLinks.Templates,
  [EPageTitle.TemplatesSystem]: ELearnMoreLinks.TemplatesSystem,
  [EPageTitle.Highlights]: ELearnMoreLinks.Highlights,
  [EPageTitle.Integrations]: ELearnMoreLinks.Integrations,
  [EPageTitle.Team]: ELearnMoreLinks.Team,
};

export interface IPageTitleProps {
  titleId: EPageTitle;
  withUnderline?: boolean;
  size?: THeaderSize;
  className?: string;
  mbSize?: string;
  isFromTableView?: boolean;
}

export function PageTitle({
  titleId,
  size = '4',
  className,
  withUnderline = true,
  mbSize,
  isFromTableView,
}: IPageTitleProps) {
  const { formatMessage } = useIntl();

  return (
    <div className={classnames(styles['container'], mbSize && styles[`is-mb-${mbSize}`], className)}>
      <Header size={size} tag="h1" className={styles['page-title']} withUnderline={withUnderline}>
        {formatMessage({ id: titleId })}
        <Tooltip
          content={
            <>
              {formatMessage({ id: tooltipTextMap[titleId] })}

              {learnMoreLinkMap[titleId] && (
                <a href={learnMoreLinkMap[titleId]} target="_blank" rel="noreferrer" className={styles['learn-more']}>
                  {formatMessage({ id: 'workflow-highlights.title-tooltip-learn-more' })}
                </a>
              )}
            </>
          }
          containerClassName={styles['tooltip-container']}
          contentClassName={isFromTableView ? styles['tooltip-content-table-view'] : ''}
          placement="bottom"
          appendTo={isFromTableView ? () => document.body : undefined}
        >
          <span className={styles['tooltip-icon']}>
            <FilledInfoIcon />
          </span>
        </Tooltip>
      </Header>
    </div>
  );
}

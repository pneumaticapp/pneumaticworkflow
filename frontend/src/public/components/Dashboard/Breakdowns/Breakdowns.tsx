/* eslint-disable react/button-has-type */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { Button, Placeholder } from '../../UI';
import { EDashboardModes, TDashboardBreakdownItem } from '../../../types/redux';
import { isArrayWithItems } from '../../../utils/helpers';
import { ILoadBreakdownTasksPayload, IOpenRunWorkflowPayload } from '../../../redux/actions';

import { DashboardPlaceholderIcon } from '../DashboardPlaceholderIcon';
import { BreakdownItem } from './BreakdownItem';
import { BreakdownsSkeleton } from './BreakdownsSkeleton';

import styles from './Breakdowns.css';

export interface IBreakdownsProps {
  mode: EDashboardModes;
  isLoading?: boolean;
  settingsChanged: boolean;
  breakdownItems: TDashboardBreakdownItem[];
  openSelectTemplateModal(): void;
  loadBreakdownTasks(payload: ILoadBreakdownTasksPayload): void;
  openRunWorkflowModalOnDashboard(payload: IOpenRunWorkflowPayload): void;
}

export function Breakdowns({
  mode,
  isLoading,
  settingsChanged,
  breakdownItems,
  openSelectTemplateModal,
  loadBreakdownTasks,
  openRunWorkflowModalOnDashboard,
}: IBreakdownsProps) {
  const { formatMessage } = useIntl();

  const renderContent = () => {
    const renderSkeleton = () => Array.from([1, 2, 3], (key) => <BreakdownsSkeleton key={key} />);

    if (isLoading) {
      return renderSkeleton();
    }

    if (!isArrayWithItems(breakdownItems)) {
      return renderPlaceholder();
    }

    return breakdownItems.map((breakdownItem) => (
      <BreakdownItem
        key={breakdownItem.templateId}
        breakdown={breakdownItem}
        mode={mode}
        loadBreakdownTasks={loadBreakdownTasks}
        openRunWorkflowModalOnDashboard={openRunWorkflowModalOnDashboard}
      />
    ));
  };

  const renderPlaceholder = () => {
    if (settingsChanged) {
      return (
        <Placeholder
          mood="bad"
          Icon={DashboardPlaceholderIcon}
          title={formatMessage({ id: 'dashboard.placeholder-empty-search-title' })}
          description={formatMessage({ id: 'dashboard.placeholder-empty-search-description' })}
        />
      );
    }

    if (mode === EDashboardModes.Tasks) {
      return (
        <Placeholder
          mood="neutral"
          Icon={DashboardPlaceholderIcon}
          title={formatMessage({ id: 'dashboard.placeholder-empty-list-title' })}
          description={formatMessage({ id: 'dashboard-tasks.placeholder-empty-list-description' })}
        />
      );
    }

    const placeholderFooter = (
      <div className={styles['placeholder']}>
        <Button
          type="button"
          size="sm"
          buttonStyle="yellow"
          label={formatMessage({ id: 'dashboard.placeholder-new-template-button' })}
          onClick={() => {}}
          className={styles['placeholder__new-template']}
        />
        <button className="cancel-button" onClick={openSelectTemplateModal}>
          {formatMessage({ id: 'dashboard.placeholder-run-workflow-button' })}
        </button>
      </div>
    );

    return (
      <Placeholder
        mood="neutral"
        Icon={DashboardPlaceholderIcon}
        title={formatMessage({ id: 'dashboard.placeholder-empty-list-title' })}
        description={formatMessage({ id: 'dashboard-workflows.placeholder-empty-list-description' })}
        footer={placeholderFooter}
      />
    );
  };

  return <div className={styles.container}>{renderContent()}</div>;
}

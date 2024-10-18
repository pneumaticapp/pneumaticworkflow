import * as React from 'react';
import * as classnames from 'classnames';
import { CellProps } from 'react-table';
import { Link } from 'react-router-dom';

import { isArrayWithItems } from '../../../../../../../utils/helpers';
import { MoreIcon, UrgentColorIcon } from '../../../../../../icons';
import { Dropdown, Tooltip } from '../../../../../../UI';
import { IWorkflowControllsProps, WorkflowControlls } from '../../../../../WorkflowControlls';
import { TableColumns } from '../../../types';
import { getWorkflowDetailedRoute } from '../../../../../../../utils/routes';

import styles from './WorkflowColumn.css';

type TProps = Pick<IWorkflowControllsProps,
  | 'onWorkflowDeleted'
  | 'onWorkflowEnded'
  | 'onWorkflowResumed'
  | 'onWorkflowSnoozed'>
  & React.PropsWithChildren<CellProps<TableColumns, TableColumns['workflow']>>
  & {
    handleOpenModal(): void;
  };

export function WorkflowColumn({
  value: workflow,
  onWorkflowDeleted,
  onWorkflowEnded,
  onWorkflowResumed,
  onWorkflowSnoozed,
  handleOpenModal,
}: TProps) {
  const [isUrgent, setIsUrgent] = React.useState(workflow.isUrgent);

  const renderDropdown = () => {
    return (
      <WorkflowControlls
        workflow={workflow}
        onWorkflowEnded={onWorkflowEnded}
        onWorkflowSnoozed={onWorkflowSnoozed}
        onWorkflowDeleted={onWorkflowDeleted}
        onWorkflowResumed={onWorkflowResumed}
        onChangeUrgent={setIsUrgent}
      >
        {controllOptions => {
          if (!isArrayWithItems(controllOptions)) {
            return null;
          }

          return (
            <Dropdown
              renderToggle={isOpen => (
                <MoreIcon
                  className={classnames(styles['card-more'], isOpen && styles['card-more_active'])}
                />
              )}
              options={controllOptions}
              direction="left"
            />
          );
        }}
      </WorkflowControlls>
    );
  }

  const onClickLink: React.MouseEventHandler<HTMLAnchorElement> = event => {
    event.preventDefault();
    handleOpenModal();
  }

  return (
    <div className={styles['container']}>
      <div className={styles['dropdown-wrapper']}>
        {renderDropdown()}
      </div>

      <div className={styles['urgent-wrapper']}>
        {isUrgent && <UrgentColorIcon />}
      </div>

      <Tooltip content={workflow.name} containerClassName={styles['workflow-link-tooltip']}>
        <span className={styles['workflow-link-tooltip__content']}>
          <Link
            to={getWorkflowDetailedRoute(workflow.id)}
            className={styles['workflow-link']}
            onClick={onClickLink}
          >
            {workflow.name}
          </Link>
        </span>
      </Tooltip>
    </div>
  );
}

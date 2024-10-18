import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ITemplateTask } from '../../../types/template';
import { ArrowDownIcon, ArrowUpIcon, ClockIcon, EditIcon, MoreIcon, TrashIcon, UnionIcon } from '../../icons';
import { Dropdown, TDropdownOption } from '../../UI';
import { TTaskFormPart } from '../types';

import styles from './TaskMenu.css';

interface ITaskMenuProps {
  tasksCount?: number;
  task: ITemplateTask;
  isTaskOpen: boolean;
  removeTask(): void;
  cloneTask(): void;
  addDelay(): void;
  moveTaskDown(): void;
  moveTaskUp(): void;
  toggleIsOpenTask(task: ITemplateTask): void;
  setScrollTarget(defaultOpenTaskFormPart: TTaskFormPart): void;
}

export function TaskMenu({
  tasksCount,
  task,
  isTaskOpen,
  removeTask,
  cloneTask,
  addDelay,
  moveTaskDown,
  moveTaskUp,
  toggleIsOpenTask,
  setScrollTarget,
}: ITaskMenuProps) {
  const { formatMessage } = useIntl();

  const handleOptionClick = (handler: () => void) =>  (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const isFirstTask = task.number === 1;
  const isLastTask = task.number === tasksCount;
  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'template.move-up' }),
      onClick: handleOptionClick(moveTaskUp),
      Icon: ArrowUpIcon,
      size: 'sm',
      isHidden: isFirstTask,
    },
    {
      label: formatMessage({ id: 'template.move-down' }),
      onClick: handleOptionClick(moveTaskDown),
      Icon: ArrowDownIcon,
      size: 'sm',
      isHidden: isLastTask,
    },
    {
      label: formatMessage({ id: 'template.add-delay' }),
      onClick: handleOptionClick(addDelay),
      Icon: ClockIcon,
      size: 'sm',
      isHidden: isFirstTask,
    },
    {
      label: formatMessage({ id: 'template.task-edit' }),
      onClick: handleOptionClick(() => {
        setScrollTarget(null);
        toggleIsOpenTask(task);
      }),
      Icon: EditIcon,
      size: 'sm',
      isHidden: isTaskOpen,
    },
    {
      label: formatMessage({ id: 'template.task-close' }),
      onClick: handleOptionClick(() => {
        setScrollTarget(null);
        toggleIsOpenTask(task);
      }),
      size: 'sm',
      isHidden: !isTaskOpen,
    },
    {
      label: formatMessage({ id: 'template.task-clone' }),
      onClick: handleOptionClick(cloneTask),
      Icon: UnionIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'template.task-remove' }),
      onClick: handleOptionClick(removeTask),
      Icon: TrashIcon,
      color: 'red',
      withConfirmation: true,
      withUpperline: true,
      size: 'sm',
    },
  ];

  return (
    <div className={styles['card-more-container']}>
      <Dropdown
        renderToggle={isOpen => (
          <MoreIcon
            className={classnames(styles['card-more'], isOpen && styles['card-more_active'])}
          />
        )}
        options={dropdownOptions}
      />
    </div>
  );
}

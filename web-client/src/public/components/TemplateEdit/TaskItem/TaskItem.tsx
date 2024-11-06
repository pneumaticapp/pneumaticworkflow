/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getPluralNoun } from '../../../utils/helpers';
import { formatDuration, formatDurationMonths, isEmptyDuration } from '../../../utils/dateTime';
import { ITemplateTask } from '../../../types/template';
import { getConditionsCount } from './utlils/getConditionsCount';
import { ClockIcon } from '../../icons';

import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { TaskItemUsers } from './TaskItemUsers';
import { ETaskFormParts } from '../types';
import { getVariables } from '../TaskForm/utils/getTaskVariables';
import { getKickoff, getTemplateTasks } from '../../../redux/selectors/template';
import { RichText } from '../../RichText';

import styles from '../TemplateEdit.css';

export interface ITaskItemProps {
  task: ITemplateTask;
  isSubscribed?: boolean;
  toggleIsOpenTask(): void;
  setScrollTarget(target: ETaskFormParts): void;
}

const DUE_IN_TEMPLATE = 'D[d] H[h] m[m]';

export const TaskItem = ({ task, isSubscribed, toggleIsOpenTask, setScrollTarget }: ITaskItemProps) => {
  const { formatMessage } = useIntl();

  const kickoff = useSelector(getKickoff);
  const tasks = useSelector(getTemplateTasks);
  const allVariables = getVariables({ kickoff, tasks });

  const handleClickOnClock = () => {
    setScrollTarget(ETaskFormParts.DueIn);
    toggleIsOpenTask();
  };

  const renderDueIn = () => {
    const { duration, durationMonths, ruleTarget } = task.rawDueDate;
    const isNoDuration = (!duration || isEmptyDuration(duration)) && !durationMonths;

    if (isNoDuration || !ruleTarget) {
      return null;
    }

    const durationFormat = formatDuration(duration, DUE_IN_TEMPLATE);
    const durationMonthsFormat = formatDurationMonths(durationMonths);
    const totalDuration = `${durationMonthsFormat} ${durationFormat}`;

    return (
      <span className={styles['task-preview-due-in']} onClick={handleClickOnClock}>
        {formatMessage({ id: 'tasks.task-due-date-duration' }, { duration: totalDuration })}
        <ClockIcon className={styles['task-preview-due-in__icon']} />
      </span>
    );
  };

  const handleClickOnUsers = () => {
    setScrollTarget(ETaskFormParts.AssignPerformers);
    toggleIsOpenTask();
  };

  const handleClickOnFields = () => {
    setScrollTarget(ETaskFormParts.Fields);
    toggleIsOpenTask();
  };

  const handleClickOnConditions = () => {
    setScrollTarget(ETaskFormParts.Conditions);
    toggleIsOpenTask();
  };

  const renderConditionsInfo = () => {
    const conditionsCounter = getConditionsCount(task.conditions);
    const conditionsInfoText = getPluralNoun({
      counter: conditionsCounter,
      single: formatMessage({ id: 'tasks.task-conditions-single' }),
      plural: formatMessage({ id: 'tasks.task-conditions-plural' }),
      includeCounter: conditionsCounter !== 0,
    });

    if (conditionsCounter > 0) {
      return (
        <span className={styles['task_view__conditions']} onClick={handleClickOnConditions}>
          {conditionsInfoText}
        </span>
      );
    }

    if (!isSubscribed) {
      return (
        <span className={styles['task_view__conditions-gold']} role="button" onClick={handleClickOnConditions}>
          {conditionsInfoText}
        </span>
      );
    }

    return null;
  };

  return (
    <div id={`task-form-${task.number}`} className={styles['task_view']} key={task.number}>
      <div className={styles['task__data-wrapper']}>
        <div className={styles['task_view-title']} onClick={toggleIsOpenTask}>
          <RichText text={task.name} variables={allVariables} isMarkdownMode={false} />
        </div>

        {task.description && (
          <div className={styles['task_view-description']} onClick={toggleIsOpenTask}>
            <RichText text={task.description} variables={allVariables} />
          </div>
        )}

        <div className={styles['task-preview-performers']}>
          <div className={styles['task-preview-performers__inner']}>
            <TaskItemUsers task={task} onClick={handleClickOnUsers} />
            {renderDueIn()}
          </div>
        </div>

        <div className={styles['task-preview-outputs']}>
          <ExtraFieldsLabels extraFields={task.fields} onClick={handleClickOnFields} />

          {renderConditionsInfo()}
        </div>
      </div>
    </div>
  );
};

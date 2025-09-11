import React from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { getSubscriptionPlan, getIsUserSubsribed } from '../../../redux/selectors/user';
import { getConditionsCount } from '../TaskItem/utlils/getConditionsCount';
import { ESubscriptionPlan } from '../../../types/account';
import { ITemplateTask } from '../../../types/template';
import { EConditionAction } from '../TaskForm/Conditions/types';

import styles from '../TemplateEdit.css';
import { getTriplePlural } from '../../../utils/helpers';

interface ITaskRenderConditionsInfoProps {
  task: ITemplateTask;
  onClick: () => void;
  isInTaskForm?: boolean;
  isStartTask?: boolean;
}

export const TaskRenderConditionsInfo = ({
  task: { conditions },
  onClick,
  isInTaskForm,
  isStartTask,
}: ITaskRenderConditionsInfoProps) => {
  const { formatMessage } = useIntl();
  const billingPlan = useSelector(getSubscriptionPlan);
  const isSubscribed = useSelector(getIsUserSubsribed);

  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;
  const startTaskCondition = conditions.find((condition) => condition.action === EConditionAction.StartTask);
  const checkIfConditions = conditions.filter((condition) => condition.action !== EConditionAction.StartTask);

  const conditionsCounter = isStartTask ? startTaskCondition?.rules.length : getConditionsCount(checkIfConditions);

  const startAfterConditionText = getTriplePlural({
    counter: conditionsCounter,
    forms: [
      'tasks.task-starts-after-title-single',
      'tasks.task-starts-after-title-plural-1',
      'tasks.task-starts-after-title-plural-2',
    ],
    formatMessage,
  });

  const checkIfConditionsText = getTriplePlural({
    counter: conditionsCounter,
    forms: [
      'tasks.task-check-if-title-single',
      'tasks.task-check-if-title-plural-1',
      'tasks.task-check-if-title-plural-2',
    ],
    formatMessage,
  });

  const conditionsInfoText = isStartTask ? startAfterConditionText : checkIfConditionsText;

  if (conditionsCounter && conditionsCounter > 0) {
    return (
      <span
        className={classNames(styles['task_view__conditions'], !isInTaskForm && styles['task_view__conditions_m-4'])}
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onClick();
          }
        }}
      >
        {conditionsInfoText}
      </span>
    );
  }

  if (!accessConditions) {
    return (
      <span
        className={styles['task_view__conditions-gold']}
        role="button"
        onClick={onClick}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onClick();
          }
        }}
      >
        {conditionsInfoText}
      </span>
    );
  }

  return null;
};

import React from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { getSubscriptionPlan, getIsUserSubsribed } from '../../../redux/selectors/user';
import { getPluralNoun } from '../../../utils/helpers';
import { getConditionsCount } from '../TaskItem/utlils/getConditionsCount';
import { ESubscriptionPlan } from '../../../types/account';
import { ITemplateTask } from '../../../types/template';

import styles from '../TemplateEdit.css';

interface ITaskRenderConditionsInfoProps {
  task: ITemplateTask;
  onClick: () => void;
  isInTaskForm?: boolean;
}

export const TaskRenderConditionsInfo = ({
  task: { conditions },
  onClick,
  isInTaskForm,
}: ITaskRenderConditionsInfoProps) => {
  const billingPlan = useSelector(getSubscriptionPlan);
  const isSubscribed = useSelector(getIsUserSubsribed);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;

  const { formatMessage } = useIntl();
  const conditionsCounter = getConditionsCount(conditions);

  const conditionsInfoText = getPluralNoun({
    counter: conditionsCounter,
    single: formatMessage({ id: 'tasks.task-conditions-single' }),
    plural: formatMessage({ id: 'tasks.task-conditions-plural' }),
    includeCounter: conditionsCounter !== 0,
  });

  if (conditionsCounter > 0) {
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

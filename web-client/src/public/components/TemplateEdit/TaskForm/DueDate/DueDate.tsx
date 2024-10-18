import * as React from 'react';
import { useIntl } from 'react-intl';

import { IDueDate, IKickoff, ITemplateTask } from '../../../../types/template';
import { DropdownList, Duration } from '../../../UI';

import { getRuleTargetOptions, TRuleTargetOption } from './utils/getRuleTargetOptions';
import { getRulePrepositionOptions, TRulePrepositionOption } from './utils/getRulePrepositionOptions';
import { useUpdatePreposition } from './hooks/useUpdatePreposition';

import styles from './DueDate.css';

interface IDueInProps {
  currentTask: ITemplateTask;
  tasks: ITemplateTask[];
  kickoff: IKickoff;
  onChange(value: IDueDate): void;
  dueDate: ITemplateTask['rawDueDate'];
}

type TDueDateKeys = keyof ITemplateTask['rawDueDate'];
export function DueDate({
  dueDate,
  currentTask,
  tasks,
  kickoff,
  onChange,
}: IDueInProps) {
  const { formatMessage } = useIntl();

  const prepositionOptions = React.useMemo(() => {
    return getRulePrepositionOptions(dueDate.ruleTarget)
  }, [dueDate.ruleTarget]);

  const [
    systemRules,
    dateFieldsRules,
    tasksRules,
  ] = React.useMemo(() => {
    return getRuleTargetOptions(
      currentTask,
      tasks,
      kickoff,
    );
  }, [tasks, kickoff]);

  const currentPrepositionOption = React.useMemo(() => {
    return prepositionOptions.find(rule => rule.rulePreposition === dueDate.rulePreposition) || null;
  }, [dueDate.rulePreposition]);

  const currentTargetOption = React.useMemo(() => {
    return [
      ...systemRules,
      ...dateFieldsRules,
      ...tasksRules,
    ].find(rule => rule.sourceId === dueDate.sourceId && rule.ruleTarget === dueDate.ruleTarget) || null;
  }, [dueDate.sourceId, dueDate.ruleTarget]);

  useUpdatePreposition(
    prepositionOptions,
    currentPrepositionOption,
    currentTargetOption,
    option => onChange({
      ...dueDate,
      rulePreposition: option,
    })
  );

  const handleChange = <T extends TDueDateKeys>(field: T) =>
    (value: ITemplateTask['rawDueDate'][T]) => {
      onChange({ ...dueDate, [field]: value });
    }

  return (
    <div className={styles['container']}>
      <Duration
        duration={dueDate.duration}
        durationMonths={dueDate.durationMonths}
        onEditDuration={handleChange('duration')}
        onEditDurationMonths={handleChange('durationMonths')}
      />
      <div className={styles['rule']}>
        <div className={styles['rule-preposition']}>
          <DropdownList
            isSearchable={false}
            value={currentPrepositionOption}
            onChange={(option: TRulePrepositionOption) => {
              onChange({
                ...dueDate,
                rulePreposition: option.rulePreposition,
              })
            }}
            isClearable={false}
            options={prepositionOptions}
          />
        </div>
        <div className={styles['rule-target']}>
          <DropdownList
            placeholder={formatMessage({ id: 'tasks.task-due-date-rule-placeholder' })}
            isSearchable={false}
            value={currentTargetOption}
            onChange={(option: TRuleTargetOption) => {
              onChange({
                ...dueDate,
                sourceId: option.sourceId,
                ruleTarget: option.ruleTarget,
              })
            }}
            isClearable={false}
            options={[
              {
                label: 'System events',
                options: systemRules,
              },
              {
                label: 'Date fields',
                options: dateFieldsRules,
              },
              {
                label: 'Task completed',
                options: tasksRules,
              },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

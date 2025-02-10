import React, { useState, useMemo } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { DropdownList, Duration } from '../../../UI';
import { TrashIcon } from '../../../icons';

import { IDueDate, IKickoff, ITemplateTask } from '../../../../types/template';
import { START_DURATION } from '../../constants';
import { getRuleTargetOptions, TRuleTargetOption } from './utils/getRuleTargetOptions';
import { getRulePrepositionOptions, TRulePrepositionOption } from './utils/getRulePrepositionOptions';
import { useUpdatePreposition } from './hooks/useUpdatePreposition';

import styles from './DueDate.css';
import stylesTaskForm from '../TaskForm.css';

interface IDueInProps {
  currentTask: ITemplateTask;
  tasks: ITemplateTask[];
  kickoff: IKickoff;
  onChange(value: IDueDate): void;
  dueDate: ITemplateTask['rawDueDate'];
}

type TDueDateKeys = keyof ITemplateTask['rawDueDate'];

export function DueDate({ dueDate, currentTask, tasks, kickoff, onChange }: IDueInProps) {
  const { formatMessage } = useIntl();
  const { duration, durationMonths, ruleTarget, rulePreposition, sourceId } = dueDate;
  const [isDueDate, setIsDueDate] = useState(Boolean(duration || durationMonths));

  const prepositionOptions = useMemo(() => {
    return getRulePrepositionOptions(ruleTarget);
  }, [ruleTarget]);

  const [systemRules, dateFieldsRules, tasksRules] = useMemo(() => {
    return getRuleTargetOptions(currentTask, tasks, kickoff);
  }, [tasks, kickoff]);

  const currentPrepositionOption = useMemo(() => {
    return prepositionOptions.find((rule) => rule.rulePreposition === rulePreposition) || null;
  }, [rulePreposition]);

  const currentTargetOption = useMemo(() => {
    return (
      [...systemRules, ...dateFieldsRules, ...tasksRules].find(
        (rule) => rule.sourceId === sourceId && rule.ruleTarget === ruleTarget,
      ) || null
    );
  }, [sourceId, ruleTarget]);

  useUpdatePreposition(prepositionOptions, currentPrepositionOption, currentTargetOption, (option) =>
    onChange({
      ...dueDate,
      rulePreposition: option,
    }),
  );

  const handleChange =
    <T extends TDueDateKeys>(field: T) =>
      (value: ITemplateTask['rawDueDate'][T]) => {
        onChange({ ...dueDate, [field]: value });
      };

  const removeDueDate = () => {
    setIsDueDate(false);
    onChange({
      ...dueDate,
      duration: null,
      durationMonths: null,
    });
  };

  const createrDueDate = () => {
    setIsDueDate(true);
    onChange({
      ...dueDate,
      duration: START_DURATION,
      durationMonths: 0,
    });
  };

  return (
    <div
      className={classnames(
        styles['container'],
        stylesTaskForm['taskform__box'],
        stylesTaskForm['taskform__basket-visibility'],
      )}
    >
      {!isDueDate ? (
        <button type="button" onClick={createrDueDate} className={stylesTaskForm['taskform__add-rule']}>
          {formatMessage({ id: 'templates.due-date-add' })}
        </button>
      ) : (
        <div>
          <Duration
            dueDateDuration
            duration={duration}
            durationMonths={durationMonths}
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
                  });
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
                  });
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

          <button
            type="button"
            aria-label={formatMessage({ id: 'templates.conditions.remove-condition-rule' })}
            onClick={removeDueDate}
            className={stylesTaskForm['taskform__remove-rule']}
          >
            <TrashIcon />
          </button>
        </div>
      )}
    </div>
  );
}

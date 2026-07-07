import * as React from 'react';

import { AutoSaveStatusContainer } from './AutoSaveStatus';
import { TemplateEntity } from './TemplateEntity';
import { AddEntityButton, EEntityTitle } from './AddEntityButton';
import { TemplateIntegrations } from './Integrations';
import { KickoffReduxContainer } from './KickoffRedux';
import { ConditionsBanner } from './ConditionsBanner';
import { TemplateSettings } from './TemplateSettings';
import { ITemplateTask } from '../../types/template';
import { useTemplateSaveRetry, useTemplateValidation } from './useTemplateForm';
import { TemplateValidationMessage } from './templateValidation';

import styles from './TemplateEdit.css';

type TTaskListItemProps = React.ComponentProps<typeof TemplateEntity> & { key: string };

interface ITemplateEditLayoutProps {
  accessConditions: boolean;
  sortedTasks(): ITemplateTask[];
  getTaskListItem(task: ITemplateTask, index: number, tasksLocal: ITemplateTask[]): TTaskListItemProps;
  handleAddTask(): void;
}

export function TemplateEditLayout({
  accessConditions,
  sortedTasks,
  getTaskListItem,
  handleAddTask,
}: ITemplateEditLayoutProps) {
  const tasksLocal = sortedTasks();
  const retryFailedSave = useTemplateSaveRetry();
  const { getError, isValidationVisible } = useTemplateValidation();
  const tasksErrorId = isValidationVisible ? getError('tasks') : undefined;

  return (
    <div className={styles['container']}>
      <AutoSaveStatusContainer onRetry={retryFailedSave} />

      <div className={styles['template-wrapper']}>
        <div className={styles['template-wrapper__info']}>
          <TemplateSettings />
        </div>
        <div className={styles['template-wrapper__tasks']}>
          {!accessConditions && <ConditionsBanner />}
          <div className={styles['tasks']}>
            <div className={styles['kickoff-wrapper']}>
              <KickoffReduxContainer />
            </div>
            {tasksLocal.map((task, index) => {
              const { key, ...taskProps } = getTaskListItem(task, index, tasksLocal);
              return <TemplateEntity key={key} {...taskProps} />;
            })}
            <div className={styles['add-task-section']} data-template-validation-anchor="tasks">
              <AddEntityButton
                entities={[
                  {
                    title: EEntityTitle.Task,
                    onAddEntity: handleAddTask,
                  },
                ]}
              />
              <TemplateValidationMessage messageId={tasksErrorId} className={styles['add-task-section__error']} />
            </div>
            <TemplateIntegrations />
          </div>
        </div>
      </div>
    </div>
  );
}

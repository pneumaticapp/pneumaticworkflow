import * as React from 'react';

import { AutoSaveStatusContainer } from './AutoSaveStatus';
import { TemplateEntity } from './TemplateEntity';
import { AddEntityButton, EEntityTitle } from './AddEntityButton';
import { TemplateIntegrations } from './Integrations';
import { KickoffReduxContainer } from './KickoffRedux';
import { ConditionsBanner } from './ConditionsBanner';
import { TemplateSettings } from './TemplateSettings';
import { ITemplateTask } from '../../types/template';

import styles from './TemplateEdit.css';

type TTaskListItemProps = React.ComponentProps<typeof TemplateEntity> & { key: string };

interface ITemplateEditLayoutProps {
  accessConditions: boolean;
  saveTemplate(): void;
  sortedTasks(): ITemplateTask[];
  getTaskListItem(task: ITemplateTask, index: number, tasksLocal: ITemplateTask[]): TTaskListItemProps;
  handleAddTask(): void;
}

export function TemplateEditLayout({
  accessConditions,
  saveTemplate,
  sortedTasks,
  getTaskListItem,
  handleAddTask,
}: ITemplateEditLayoutProps) {
  const tasksLocal = sortedTasks();

  return (
    <div className={styles['container']}>
      <AutoSaveStatusContainer onRetry={saveTemplate} />

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
            <AddEntityButton
              entities={[
                {
                  title: EEntityTitle.Task,
                  onAddEntity: handleAddTask,
                },
              ]}
            />
            <TemplateIntegrations />
          </div>
        </div>
      </div>
    </div>
  );
}

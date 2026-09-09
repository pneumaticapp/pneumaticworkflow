import * as React from 'react';
import { useCallback, useMemo } from 'react';

import { ITemplateClient } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { ITemplateEditorController } from '../types';
import { KickoffReduxContainer } from '../KickoffRedux';
import { WorkflowTaskFormContainer } from '../TaskForm';
import { GraphTaskEditorPanel, TemplateGraphEditor } from '../TemplateGraphEditor';
import { TGraphAddTaskIntent } from '../TemplateGraphEditor/types';
import { KICKOFF_NODE_ID } from '../TemplateGraphEditor/utils/templateToGraph';

export interface ITemplateGraphEditorViewProps {
  template: ITemplateClient;
  users: TUserListItem[];
  selectedTaskApiName: string | null;
  controller: ITemplateEditorController;
  selectTask(apiName: string | null): void;
}

export function TemplateGraphEditorView({
  template,
  users,
  selectedTaskApiName,
  controller,
  selectTask,
}: ITemplateGraphEditorViewProps) {
  const selectedTask = useMemo(
    () => controller.sortedTasks.find((task) => task.apiName === selectedTaskApiName) ?? null,
    [controller.sortedTasks, selectedTaskApiName],
  );
  const isEditorOpen = selectedTaskApiName !== null;

  const handleTaskEdit = useCallback(
    (taskApiName: string): void => {
      selectTask(taskApiName);
    },
    [selectTask],
  );

  const handleKickoffEdit = useCallback((): void => {
    selectTask(KICKOFF_NODE_ID);
  }, [selectTask]);

  const handleClose = useCallback((): void => {
    selectTask(null);
  }, [selectTask]);

  const handleAddTask = useCallback(
    (intent: TGraphAddTaskIntent): void => {
      const createdApiName = controller.addTaskFromGraph(intent);
      if (createdApiName) selectTask(createdApiName);
    },
    [controller, selectTask],
  );

  return (
    <>
      <TemplateGraphEditor
        template={template}
        onTaskEdit={handleTaskEdit}
        onKickoffEdit={handleKickoffEdit}
        onAddTask={handleAddTask}
      />
      {isEditorOpen && (
        <GraphTaskEditorPanel onClose={handleClose}>
          {selectedTaskApiName === KICKOFF_NODE_ID ? (
            <KickoffReduxContainer
              setKickoff={controller.setKickoff}
              forceOpen
              embedded
              onOpenChange={(isOpen: boolean) => {
                if (!isOpen) handleClose();
              }}
            />
          ) : (
            selectedTask && <WorkflowTaskFormContainer task={selectedTask} users={users} scrollTarget={null} embedded />
          )}
        </GraphTaskEditorPanel>
      )}
    </>
  );
}

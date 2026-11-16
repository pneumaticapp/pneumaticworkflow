import { useCallback, useMemo } from 'react';
import { debounce } from 'throttle-debounce';

import { cleanTemplateReferences } from '../utils/template';
import { moveTask } from '../utils/workflows';
import { isArrayWithItems } from '../utils/helpers';
import { ITemplateClient, ITemplateKickoffClient, ITemplateTaskClient } from '../types/template';
import { IAuthUser, ETemplateStatus } from '../types/redux';
import { EMoveDirections } from '../types/workflow';
import { getClonedTask } from '../components/TemplateEdit/utils/getClonedTask';
import { createTemplateTask } from '../components/TemplateEdit/utils/createTemplateTask';
import { getKickoffConditions } from '../components/TemplateEdit/TaskForm/Conditions/utils/getKickoffConditions';
import { getStartTaskConditions } from '../components/TemplateEdit/TaskForm/Conditions/utils/getStartTaskConditions';
import { insertGraphTask } from '../components/TemplateEdit/TemplateGraphEditor/utils/insertGraphTask';
import { TGraphAddTaskIntent } from '../components/TemplateEdit/TemplateGraphEditor/types';
import { ITemplateEditorController } from '../components/TemplateEdit/types';
import { insertTemplateTask, removeTemplateTask } from '../components/TemplateEdit/utils/templateTaskList';
import { useTemplateEditorExpandedState } from './useTemplateEditorExpandedState';
import { useTemplateTaskDelays } from './useTemplateTaskDelays';

export interface IUseTemplateEditorControllerOptions {
  template: ITemplateClient;
  authUser: IAuthUser;
  accessConditions: boolean;
  shouldOpenFirstTask: boolean;
  selectedTaskApiName: string | null;
  saveTemplate(): void;
  setTemplate(payload: ITemplateClient): void;
  setTemplateStatus(status: ETemplateStatus): void;
  setSelectedTask(apiName: string | null): void;
}

export function useTemplateEditorController({
  template,
  authUser,
  accessConditions,
  shouldOpenFirstTask,
  selectedTaskApiName,
  saveTemplate,
  setTemplate,
  setTemplateStatus,
  setSelectedTask,
}: IUseTemplateEditorControllerOptions): ITemplateEditorController {
  const { tasks } = template;
  const submitDebounced = useMemo(() => debounce(350, saveTemplate), [saveTemplate]);
  const sortedTasks = useMemo(() => [...tasks].sort((a, b) => a.number - b.number), [tasks]);
  const { openedTasks, openedDelays, toggleTask, toggleDelay } = useTemplateEditorExpandedState(
    tasks[0]?.uuid,
    shouldOpenFirstTask,
  );

  const changeTemplateField = useCallback(
    (field: keyof ITemplateClient, value: ITemplateClient[keyof ITemplateClient]): void => {
      setTemplateStatus(ETemplateStatus.Saving);

      const updatedTemplate: ITemplateClient =
        field === 'isActive'
          ? { ...template, isActive: value as boolean }
          : { ...template, [field]: value, isActive: false };
      const nextTemplate =
        field === 'kickoff' || field === 'tasks' ? cleanTemplateReferences(updatedTemplate) : updatedTemplate;

      setTemplate(nextTemplate);
      submitDebounced();
    },
    [setTemplate, setTemplateStatus, submitDebounced, template],
  );

  const changeTasks = useCallback(
    (nextTasks: ITemplateTaskClient[]): void => {
      changeTemplateField('tasks', nextTasks);
    },
    [changeTemplateField],
  );
  const { addDelay, editDelay, deleteDelay } = useTemplateTaskDelays(tasks, changeTasks, toggleDelay);

  const createTask = useCallback(
    (overrides?: Partial<ITemplateTaskClient>): ITemplateTaskClient =>
      createTemplateTask({ authUser, accessConditions, overrides }),
    [accessConditions, authUser],
  );

  const setKickoff = useCallback(
    (kickoff: ITemplateKickoffClient): void => {
      changeTemplateField('kickoff', kickoff);
    },
    [changeTemplateField],
  );

  const addTask = useCallback((): void => {
    if (!isArrayWithItems(tasks)) {
      changeTasks([createTask({ conditions: getKickoffConditions() })]);
      return;
    }

    const number = tasks.length + 1;
    const newTask = createTask({
      number,
      name: `New Step ${number}`,
      conditions: getStartTaskConditions(tasks[tasks.length - 1].apiName),
    });

    toggleTask(newTask.uuid);
    changeTasks([...tasks, newTask]);
  }, [changeTasks, createTask, tasks, toggleTask]);

  const addTaskBefore = useCallback(
    (targetTask: ITemplateTaskClient, previousTaskApiName?: string): void => {
      const newTask = createTask({
        name: `New Step ${tasks.length + 1}`,
        conditions: previousTaskApiName ? getStartTaskConditions(previousTaskApiName) : getKickoffConditions(),
      });

      changeTasks(insertTemplateTask(tasks, newTask, targetTask.number - 1));
      toggleTask(newTask.uuid);
    },
    [changeTasks, createTask, tasks, toggleTask],
  );

  const addTaskFromGraph = useCallback(
    (intent: TGraphAddTaskIntent): string | null => {
      const { tasks: nextTasks, createdApiName } = insertGraphTask(tasks, intent, createTask);
      if (!createdApiName) return null;

      changeTasks(nextTasks);
      return createdApiName;
    },
    [changeTasks, createTask, tasks],
  );

  const removeTask = useCallback(
    (targetTask: ITemplateTaskClient): void => {
      const nextTasks = removeTemplateTask(tasks, targetTask.uuid);

      if (selectedTaskApiName === targetTask.apiName) {
        setSelectedTask(null);
      }

      changeTasks(isArrayWithItems(nextTasks) ? nextTasks : [createTask()]);
    },
    [changeTasks, createTask, selectedTaskApiName, setSelectedTask, tasks],
  );

  const cloneTask = useCallback(
    (targetTask: ITemplateTaskClient): void => {
      const newTask = getClonedTask(targetTask);
      changeTasks(insertTemplateTask(tasks, newTask, targetTask.number));
      toggleTask(newTask.uuid);
    },
    [changeTasks, tasks, toggleTask],
  );

  const moveTemplateTask = useCallback(
    (from: number, direction: EMoveDirections): void => {
      const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
      changeTasks([...moveTask(from, to, tasks)].sort((a, b) => a.number - b.number));
    },
    [changeTasks, tasks],
  );

  return {
    sortedTasks,
    openedTasks,
    openedDelays,
    setKickoff,
    addTask,
    addTaskBefore,
    addTaskFromGraph,
    removeTask,
    cloneTask,
    moveTask: moveTemplateTask,
    addDelay,
    editDelay,
    deleteDelay,
    toggleTask,
    toggleDelay,
  };
}

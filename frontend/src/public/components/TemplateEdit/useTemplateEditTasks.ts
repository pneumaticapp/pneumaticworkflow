import { useState } from 'react';
import { FormikProps } from 'formik';
import { IntlShape } from 'react-intl';

import { createNewTemplateTask } from './utils/createTemplateEditTask';
import { getClonedTask } from './utils/getClonedTask';
import { getKickoffConditions } from './TaskForm/Conditions/utils/getKickoffConditions';
import { getStartTaskConditions } from './TaskForm/Conditions/utils/getStartTaskConditions';
import { START_DURATION } from './constants';
import { moveTask } from '../../utils/workflows';
import { NotificationManager } from '../UI/Notifications';
import { isArrayWithItems } from '../../utils/helpers';
import { EMoveDirections } from '../../types/workflow';
import { ITemplate, ITemplateTask } from '../../types/template';
import { TUserListItem } from '../../types/user';
import { IAuthUser } from '../../types/redux';
import { TSetFieldValue } from './useTemplateForm/types';

type TUseTemplateEditTasksParams = {
  authUser: IAuthUser;
  formik: FormikProps<ITemplate>;
  setFieldValue: TSetFieldValue;
  users: TUserListItem[];
  accessConditions: boolean;
  formatMessage: IntlShape['formatMessage'];
  isSubscribed: boolean;
};

export function useTemplateEditTasks({
  authUser,
  formik,
  setFieldValue,
  accessConditions,
  formatMessage,
  isSubscribed,
  users,
}: TUseTemplateEditTasksParams) {
  const { tasks } = formik.values;
  const [openedTasks, setOpenedTasks] = useState<Record<string, boolean>>({});
  const [openedDelays, setOpenedDelays] = useState<Record<string, boolean>>({});

  const changeTasks = (newTasks: ITemplateTask[]) => {
    setFieldValue('tasks', newTasks, false);
  };

  const openTask = (taskUUID?: string) => {
    if (!taskUUID) return;
    setOpenedTasks((prev) => ({ ...prev, [taskUUID]: true }));
  };

  const toggleIsOpenTask = (taskUUID: string) => {
    setOpenedTasks((prev) => ({ ...prev, [taskUUID]: !prev[taskUUID] }));
  };

  const toggleDelay = (taskUUID: string) => {
    setOpenedDelays((prev) => ({ ...prev, [taskUUID]: !prev[taskUUID] }));
  };

  const sortedTasks = () => [...tasks].sort((a, b) => a.number - b.number);

  const getNewTask = (templateTask?: Partial<ITemplateTask>) =>
    createNewTemplateTask(authUser, accessConditions, templateTask);

  const handleRemoveTask = (targetTask: ITemplateTask) => () => {
    const newTasks = tasks
      .filter((task) => task.uuid !== targetTask.uuid)
      .map((task, index) => ({ ...task, number: index + 1 }));

    if (!isArrayWithItems(newTasks)) {
      changeTasks([getNewTask()]);
      return;
    }

    changeTasks(newTasks);
  };

  const handleAddTask = () => {
    if (!isArrayWithItems(tasks)) {
      changeTasks([
        getNewTask({
          conditions: getKickoffConditions(),
        }),
      ]);
      return;
    }

    const newTaskNumber = tasks.length + 1;
    const newTask = getNewTask({
      number: newTaskNumber,
      name: `New Step ${newTaskNumber}`,
      conditions: getStartTaskConditions(tasks[tasks.length - 1].apiName),
    });

    toggleIsOpenTask(newTask.uuid);
    changeTasks([...tasks, newTask]);
  };

  const getTasksWithNewTask = (newTask: ITemplateTask, newTaskIndex: number) =>
    [...tasks.slice(0, newTaskIndex), newTask, ...tasks.slice(newTaskIndex)].map((task, index) => ({
      ...task,
      number: index + 1,
    }));

  const handleCloneTask = (targetTask: ITemplateTask) => () => {
    const newTask = getClonedTask(targetTask);
    changeTasks(getTasksWithNewTask(newTask, targetTask.number));
    toggleIsOpenTask(newTask.uuid);
  };

  const handleAddTaskBefore = (targetTask: ITemplateTask) => (previousTaskApiName?: string) => {
    const newTask = getNewTask({
      name: `New Step ${tasks.length + 1}`,
      conditions: previousTaskApiName ? getStartTaskConditions(previousTaskApiName) : getKickoffConditions(),
    });

    changeTasks(getTasksWithNewTask(newTask, targetTask.number - 1));
    toggleIsOpenTask(newTask.uuid);
  };

  const handleMoveTask = (from: number, direction: EMoveDirections) => () => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const movedTasks = moveTask(from, to, tasks);
    changeTasks([...movedTasks].sort((a, b) => a.number - b.number));
  };

  const handleEditTaskField =
    (targetTask: ITemplateTask) => (field: keyof ITemplateTask) => (value: ITemplateTask[keyof ITemplateTask]) => {
      changeTasks(
        tasks.map((task) => (targetTask.uuid === task.uuid ? { ...task, [field]: value } : task)),
      );
    };

  const addDelay = (targetTask: ITemplateTask) => () => {
    if (targetTask.delay) {
      NotificationManager.warning({
        message: formatMessage({ id: 'template.delay-task-has-delay-error' }),
      });
      return;
    }

    if (targetTask.number === 1) {
      NotificationManager.warning({
        message: formatMessage({ id: 'template.delay-first-task-delay-error' }),
      });
      return;
    }

    toggleDelay(targetTask.uuid);
    changeTasks(
      tasks.map((task) => (task.uuid === targetTask.uuid ? { ...task, delay: START_DURATION } : task)),
    );
  };

  const editDelay = (targetTask: ITemplateTask) => (delay: string) => {
    changeTasks(tasks.map((task) => (task.uuid === targetTask.uuid ? { ...task, delay } : task)));
  };

  const deleteDelay = (targetTask: ITemplateTask) => () => {
    if (!targetTask.delay) return;
    handleEditTaskField(targetTask)('delay')('');
  };

  const getTaskListItem = (task: ITemplateTask, index: number, tasksLocal: ITemplateTask[]) => {
    const previousTask = index > 0 ? tasksLocal[index - 1] : null;

    return {
      key: `template-entity-${task.uuid}`,
      index,
      task,
      users,
      tasksCount: tasksLocal.length,
      isSubscribed,
      removeTask: handleRemoveTask(task),
      cloneTask: handleCloneTask(task),
      addDelay: addDelay(task),
      addTaskBefore: handleAddTaskBefore(task),
      deleteDelay,
      editDelay: editDelay(task),
      isTaskOpen: Boolean(openedTasks[task.uuid]),
      isDelayOpen: Boolean(openedDelays[task.uuid]),
      toggleDelay: () => toggleDelay(task.uuid),
      handleMoveTask,
      toggleIsOpenTask: () => toggleIsOpenTask(task.uuid),
      actualPreviousTaskApiName: previousTask?.apiName,
    };
  };

  return {
    sortedTasks,
    handleAddTask,
    getTaskListItem,
    openTask,
  };
}

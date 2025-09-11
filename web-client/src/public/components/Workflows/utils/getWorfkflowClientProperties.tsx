import {
  EWorkflowStatus,
  EWorkflowTaskStatus,
  IWorkflow,
  IWorkflowClient,
  IWorkflowDetailsClient,
  IWorkflowTaskClient,
  IWorkflowTaskDelay,
} from '../../../types/workflow';

export enum EProgressbarColor {
  Yellow = '#FFC107',
  Red = '#E53D00',
  Grey = '#979795',
  Green = '#5FAD56',
}

const checkOverdueTask = (task: IWorkflowTaskClient) => {
  const defaultResult = { isOverdue: false, count: 0, dueDateTimestamp: null };
  if (!task.dueDate) return defaultResult;

  const dueDateTimestamp = Date.parse(task.dueDate);
  const isOverdue = dueDateTimestamp < Date.now();

  if (isOverdue && task.status === EWorkflowTaskStatus.Active) {
    return { isOverdue: true, count: 1, dueDateTimestamp };
  }
  if (task.overdue && task.status !== EWorkflowTaskStatus.Active) {
    return { isOverdue: false, count: -1, dueDateTimestamp };
  }

  return { isOverdue: false, count: 0, dueDateTimestamp };
};

const getStepColor = (task: IWorkflowTaskClient, status: EWorkflowStatus): EProgressbarColor | null => {
  if (status === EWorkflowStatus.Snoozed && task.status !== EWorkflowTaskStatus.Pending) {
    return EProgressbarColor.Grey;
  }
  if (
    task.status === EWorkflowTaskStatus.Completed ||
    (status === EWorkflowStatus.Finished && task.status !== EWorkflowTaskStatus.Pending)
  ) {
    return EProgressbarColor.Green;
  }
  if (task.status === EWorkflowTaskStatus.Active) {
    return task.overdue ? EProgressbarColor.Red : EProgressbarColor.Yellow;
  }

  return null;
};

export const getWorkflowAddComputedPropsToRedux = (workflow: IWorkflow): IWorkflowClient | IWorkflowDetailsClient => {
  let multipleTasksCount = 0;
  const namesMultipleTasks: Record<string, string> = {};
  const currentPerformersMap = new Map();
  let overdueTasksCount = 0;
  let oldestDeadline: number | null = null;
  let minEstimatedEndDateTsp = Infinity;
  let minDelay: IWorkflowTaskDelay | null = null;

  const formattedTasks = workflow.tasks.map((task) => {
    const newTask: IWorkflowTaskClient = {
      ...task,
      overdue: false,
      color: null,
    };

    if (newTask.status === EWorkflowTaskStatus.Active) {
      multipleTasksCount += 1;
      namesMultipleTasks[newTask.apiName] = newTask.name;
      newTask.performers.forEach((performer) => {
        currentPerformersMap.set(performer.sourceId, performer);
      });
    }

    const { isOverdue, count, dueDateTimestamp } = checkOverdueTask(newTask);
    newTask.overdue = isOverdue;
    overdueTasksCount += count;
    if (dueDateTimestamp && !oldestDeadline) {
      oldestDeadline = dueDateTimestamp;
    } else if (dueDateTimestamp && oldestDeadline) {
      oldestDeadline = dueDateTimestamp < oldestDeadline ? dueDateTimestamp : oldestDeadline;
    }

    newTask.color = getStepColor(newTask, workflow.status);

    if (
      workflow.status === EWorkflowStatus.Snoozed &&
      newTask.status === EWorkflowTaskStatus.Snoozed &&
      newTask.delay?.estimatedEndDateTsp &&
      newTask.delay.estimatedEndDateTsp < minEstimatedEndDateTsp
    ) {
      minEstimatedEndDateTsp = newTask.delay.estimatedEndDateTsp;
      minDelay = task.delay;
    }

    return newTask;
  });

  const completedTasks = formattedTasks.filter((task) => task.status === EWorkflowTaskStatus.Completed);
  const areMultipleTasks = Boolean(multipleTasksCount > 1);
  const oneActiveTaskName = multipleTasksCount === 1 ? Object.values(namesMultipleTasks)[0] : null;
  const selectedUsers = Array.from(currentPerformersMap.values());

  const tasksCountWithoutSkipped = workflow.tasks.length;
  const areOverdueTasks = Boolean(overdueTasksCount);
  const formattedOldestDeadline = oldestDeadline && new Date(oldestDeadline).toISOString();

  return {
    ...workflow,
    tasks: formattedTasks,
    completedTasks,

    areMultipleTasks,
    namesMultipleTasks,
    oneActiveTaskName,
    selectedUsers,

    tasksCountWithoutSkipped,
    minDelay,
    areOverdueTasks,
    oldestDeadline: formattedOldestDeadline,
  };
};

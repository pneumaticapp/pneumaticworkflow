import { getUserFullName } from '../../../utils/users';
import { createPerformerApiName, createTaskApiName, createUUID } from '../../../utils/createId';
import { createEmptyTaskDueDate } from '../../../utils/dueDate/createEmptyTaskDueDate';
import { ITemplateTaskClient, ETaskPerformerType } from '../../../types/template';
import { IAuthUser } from '../../../types/redux';
import { getEmptyConditions } from '../TaskForm/Conditions/utils/getEmptyConditions';

export interface ICreateTemplateTaskOptions {
  authUser: IAuthUser;
  accessConditions: boolean;
  overrides?: Partial<ITemplateTaskClient>;
}

export function createTemplateTask({
  authUser,
  accessConditions,
  overrides,
}: ICreateTemplateTaskOptions): ITemplateTaskClient {
  const taskApiName = createTaskApiName();

  return {
    apiName: taskApiName,
    delay: null,
    description: '',
    name: 'New Step',
    number: 1,
    fields: [],
    fieldsets: [],
    rawPerformers: [
      {
        apiName: createPerformerApiName(),
        label: getUserFullName(authUser),
        type: ETaskPerformerType.User,
        sourceId: String(authUser.id),
      },
    ],
    uuid: createUUID(),
    requireCompletionByAll: false,
    skipForStarter: false,
    conditions: getEmptyConditions(accessConditions),
    rawDueDate: createEmptyTaskDueDate(taskApiName),
    checklists: [],
    ...overrides,
    revertTask: null,
    ancestors: [],
  };
}

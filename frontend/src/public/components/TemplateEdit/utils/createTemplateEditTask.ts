import { DEFAULT_TEMPLATE_NAME } from '../constants';
import { getKickoffConditions } from '../TaskForm/Conditions/utils/getKickoffConditions';
import { getEmptyConditions } from '../TaskForm/Conditions/utils/getEmptyConditions';
import { createEmptyTaskDueDate } from '../../../utils/dueDate/createEmptyTaskDueDate';
import { getEmptyKickoff, getNormalizedTemplateOwners } from '../../../utils/template';
import { createOwnerApiName, createPerformerApiName, createTaskApiName, createUUID } from '../../../utils/createId';
import { getUserFullName } from '../../../utils/users';
import {
  ETaskPerformerType,
  ETemplateOwnerRole,
  ETemplateOwnerType,
  ITemplate,
  ITemplateTask,
} from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { IAuthUser } from '../../../types/redux';

export function createNewTemplateTask(
  authUser: IAuthUser,
  accessConditions: boolean,
  templateTask?: Partial<ITemplateTask>,
): ITemplateTask {
  const taskApiName = createTaskApiName();

  return {
    apiName: taskApiName,
    delay: null,
    description: '',
    name: 'New Step',
    number: 1,
    fields: [],
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
    ...templateTask,
    revertTask: null,
    ancestors: [],
  };
}

export function createEmptyTemplate(
  authUser: IAuthUser,
  users: TUserListItem[],
  accessConditions: boolean,
): ITemplate {
  return {
    description: '',
    kickoff: getEmptyKickoff(),
    name: DEFAULT_TEMPLATE_NAME,
    tasks: [
      createNewTemplateTask(authUser, accessConditions, {
        name: 'First Step',
        number: 1,
        conditions: getKickoffConditions(),
      }),
    ],
    isActive: false,
    finalizable: false,
    dateUpdated: null,
    updatedBy: null,
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    tasksCount: 1,
    performersCount: 0,
    owners: getNormalizedTemplateOwners(
      [
        {
          sourceId: String(authUser.id),
          type: ETemplateOwnerType.User,
          apiName: createOwnerApiName(),
          role: ETemplateOwnerRole.Owner,
        },
      ],
      accessConditions,
      users,
    ),
    wfNameTemplate: '{{date}} — {{template-name}}',
  } as ITemplate;
}

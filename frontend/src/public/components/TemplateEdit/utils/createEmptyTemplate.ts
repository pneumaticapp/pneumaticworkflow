import { ETemplateOwnerRole, ETemplateOwnerType, ITemplateClient } from '../../../types/template';
import { IAuthUser } from '../../../types/redux';
import { TUserListItem } from '../../../types/user';
import { createOwnerApiName } from '../../../utils/createId';
import { getEmptyKickoff, getNormalizedTemplateOwners } from '../../../utils/template';
import { DEFAULT_TEMPLATE_NAME } from '../constants';
import { getKickoffConditions } from '../TaskForm/Conditions/utils/getKickoffConditions';
import { createTemplateTask } from './createTemplateTask';

export interface ICreateEmptyTemplateOptions {
  authUser: IAuthUser;
  accessConditions: boolean;
  users: TUserListItem[];
  name?: string;
  firstStepName?: string;
}

export function createEmptyTemplate({
  authUser,
  accessConditions,
  users,
  name = DEFAULT_TEMPLATE_NAME,
  firstStepName = 'First Step',
}: ICreateEmptyTemplateOptions): ITemplateClient {
  return {
    description: '',
    kickoff: getEmptyKickoff(),
    name,
    tasks: [
      createTemplateTask({
        authUser,
        accessConditions,
        overrides: {
          name: firstStepName,
          number: 1,
          conditions: getKickoffConditions(),
        },
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
    completionNotification: false,
    reminderNotification: false,
  };
}

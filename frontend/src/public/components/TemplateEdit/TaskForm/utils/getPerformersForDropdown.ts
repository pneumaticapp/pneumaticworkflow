import { IntlShape } from 'react-intl';
import { EExtraFieldType, ETaskPerformerType, ITemplateTaskPerformer } from '../../../../types/template';
import { TUserListItem } from '../../../../types/user';
import { getUserFullName } from '../../../../utils/users';
import { TTaskVariable } from '../../types';
import { EOptionTypes, TUsersDropdownOption } from '../../../UI/form/UsersDropdown';
import { IGroup } from '../../../../redux/team/types';

export function getPerformersForDropdown(
  users: TUserListItem[],
  groups: IGroup[],
  variables: TTaskVariable[],
  formatMessage: IntlShape['formatMessage'],
): TUsersDropdownOption[] {
  const userPeformers: (Omit<ITemplateTaskPerformer, 'apiName'> & TUsersDropdownOption)[] = users.map((user) => ({
    id: user.id,
    optionType: EOptionTypes.User,
    firstName: '',
    lastName: '',
    type: ETaskPerformerType.User,
    sourceId: String(user.id),
    label: getUserFullName(user),
    value: String(user.id),
  }));

  const outputUsersPerformers: TUsersDropdownOption[] = variables
    .filter((variable) => variable.type === EExtraFieldType.User)
    .map(({ apiName, title }) => ({
      id: 0,
      optionType: EOptionTypes.Field,
      firstName: '',
      lastName: '',
      type: ETaskPerformerType.OutputUser,
      sourceId: apiName,
      label: title,
      value: apiName,
    }));

  const groupsPerformers: (Omit<ITemplateTaskPerformer, 'apiName'> & TUsersDropdownOption)[] = groups.map((group) => ({
    id: group.id,
    optionType: EOptionTypes.Group,
    firstName: '',
    lastName: '',
    type: ETaskPerformerType.UserGroup,
    sourceId: String(group.id),
    label: group.name,
    value: String(group.id),
  }));

  const workflowStarterPerformers: Omit<ITemplateTaskPerformer, 'apiName'> & TUsersDropdownOption = {
    id: 0,
    optionType: EOptionTypes.Field,
    firstName: '',
    lastName: '',
    type: ETaskPerformerType.WorkflowStarter,
    sourceId: null,
    label: formatMessage({ id: 'tasks.task-workflow-starter' }),
    value: String(null),
  };

  return [workflowStarterPerformers, ...groupsPerformers, ...outputUsersPerformers, ...userPeformers];
}

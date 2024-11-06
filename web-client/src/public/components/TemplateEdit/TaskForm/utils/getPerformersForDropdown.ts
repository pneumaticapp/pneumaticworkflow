import { IntlShape } from 'react-intl';
import { EExtraFieldType, ETaskPerformerType, ITemplateTaskPerformer } from '../../../../types/template';
import { TUserListItem } from '../../../../types/user';
import { getUserFullName } from '../../../../utils/users';
import { TTaskVariable } from '../../types';
import { EOptionTypes, TUsersDropdownOption } from '../../../UI/form/UsersDropdown';

export function getPerformersForDropdown(
  users: TUserListItem[],
  variables: TTaskVariable[],
  formatMessage: IntlShape['formatMessage'],
): TUsersDropdownOption[] {
  const userPeformers: (ITemplateTaskPerformer & TUsersDropdownOption)[] = users
    .map(user => ({
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
    .filter(variable => variable.type === EExtraFieldType.User)
    .map((({ apiName, title }) => ({
      id: 0,
      optionType: EOptionTypes.Field,
      firstName: '',
      lastName: '',
      type: ETaskPerformerType.OutputUser,
      sourceId: apiName,
      label: title,
      value: apiName,
    })));

  const workflowStarterPerformers: ITemplateTaskPerformer & TUsersDropdownOption = {
    id: 0,
    optionType: EOptionTypes.Field,
    firstName: '',
    lastName: '',
    type: ETaskPerformerType.WorkflowStarter,
    sourceId: null,
    label: formatMessage({ id: 'tasks.task-workflow-starter' }),
    value: String(null),
  };

  return [
    workflowStarterPerformers,
    ...outputUsersPerformers,
    ...userPeformers,
  ];
}

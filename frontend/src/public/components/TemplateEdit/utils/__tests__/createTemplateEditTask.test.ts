import { IAuthUser } from '../../../../types/redux';
import { TUserListItem } from '../../../../types/user';
import { ETemplateOwnerRole } from '../../../../types/template';
import { createEmptyTemplate, createNewTemplateTask } from '../createTemplateEditTask';

const authUser = {
  id: 1,
  firstName: 'Test',
  lastName: 'User',
} as IAuthUser;

describe('createNewTemplateTask', () => {
  it('sets rawDueDate.sourceId from the final apiName when caller overrides apiName', () => {
    const task = createNewTemplateTask(authUser, true, { apiName: 'custom-task-api-name' });

    expect(task.apiName).toBe('custom-task-api-name');
    expect(task.rawDueDate.sourceId).toBe('custom-task-api-name');
  });
});

describe('createEmptyTemplate', () => {
  const users = [
    { id: 1, firstName: 'Test', lastName: 'User' },
    { id: 2, firstName: 'Other', lastName: 'User' },
  ] as TUserListItem[];

  it('keeps the creator as the sole owner on free plans with accessConditions enabled', () => {
    const template = createEmptyTemplate(authUser, users, true);

    expect(template.owners).toHaveLength(1);
    expect(template.owners[0]).toMatchObject({
      sourceId: '1',
      role: ETemplateOwnerRole.Owner,
    });
  });
});

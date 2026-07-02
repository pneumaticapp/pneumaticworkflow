import { IAuthUser } from '../../../../types/redux';
import { createNewTemplateTask } from '../createTemplateEditTask';

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

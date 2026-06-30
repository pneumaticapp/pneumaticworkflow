import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeTemplateTaskClient } from '../../../../../__stubs__/templates.factory';
import { ETaskPerformerType, ITemplateTaskClient } from '../../../../../types/template';
import { TUserListItem } from '../../../../../types/user';
import { IGroup } from '../../../../../redux/team/types';
import { makeUser } from '../../../../../__stubs__/users.factory';
import { makeGroup } from '../../../../../__stubs__/team.factory';
import { getPerformersForDropdown } from '../getPerformersForDropdown';
import { EOptionTypes } from '../../../../UI/form/UsersDropdown';

jest.mock('../../../../../utils/users', () => ({
  getUserFullName: jest.fn((u: { firstName?: string; lastName?: string }) => `${u.firstName} ${u.lastName}`),
}));
describe('getPerformersForDropdown', () => {
  const formatMsg = (id: string, values?: Record<string, string>) => intlMock.formatMessage({ id }, values);
  const MANAGER_LABEL = (step: string) => formatMsg('tasks.task-manager-of-step', { step });

  const makeTask = (overrides: Partial<ITemplateTaskClient> = {}) => makeTemplateTaskClient({
    name: 'First Step',
    ...overrides,
  });

  describe('Manager options', () => {
    it('generates a Manager option for each step except the current one', () => {
      const currentTask = makeTask({ apiName: 'task-2', name: 'Second Step', number: 2 });
      const tasks = [
        makeTask({ apiName: 'task-1', name: 'First Step', number: 1 }),
        currentTask,
        makeTask({ apiName: 'task-3', name: 'Third Step', number: 3 }),
      ];

      const result = getPerformersForDropdown(
        [],
        [],
        [],
        intlMock.formatMessage,
        currentTask,
        tasks,
      );

      const managerOptions = result.filter((o) => o.optionType === EOptionTypes.Manager);

      expect(managerOptions).toHaveLength(2);
      expect(managerOptions[0]).toMatchObject({
        type: ETaskPerformerType.Manager,
        sourceId: 'task-1',
        label: MANAGER_LABEL('First Step'),
        optionType: EOptionTypes.Manager,
      });
      expect(managerOptions[1]).toMatchObject({
        type: ETaskPerformerType.Manager,
        sourceId: 'task-3',
        label: MANAGER_LABEL('Third Step'),
      });
    });

    it('returns empty Manager options array when tasks are not provided', () => {
      const result = getPerformersForDropdown(
        [],
        [],
        [],
        intlMock.formatMessage,
      );

      const managerOptions = result.filter((o) => o.optionType === EOptionTypes.Manager);

      expect(managerOptions).toHaveLength(0);
    });

    it('returns empty Manager options array for a single step', () => {
      const task = makeTask();

      const result = getPerformersForDropdown(
        [],
        [],
        [],
        intlMock.formatMessage,
        task,
        [task],
      );

      const managerOptions = result.filter((o) => o.optionType === EOptionTypes.Manager);

      expect(managerOptions).toHaveLength(0);
    });

    it('generates unique values for user and group with the same id', () => {
      const users: TUserListItem[] = [makeUser({ id: 5, firstName: 'John', lastName: 'Doe' })];
      const groups: IGroup[] = [makeGroup({ id: 5, name: 'Team A' })];

      const result = getPerformersForDropdown(users, groups, [], intlMock.formatMessage);

      const userOption = result.find((option) => option.optionType === EOptionTypes.User);
      const groupOption = result.find((option) => option.optionType === EOptionTypes.Group);

      expect(userOption?.value).toBe('user-5');
      expect(groupOption?.value).toBe('group-5');
    });

    it('Manager option has a unique value with manager- prefix', () => {
      const currentTask = makeTask({ apiName: 'task-2', number: 2 });
      const tasks = [makeTask(), currentTask];

      const result = getPerformersForDropdown(
        [],
        [],
        [],
        intlMock.formatMessage,
        currentTask,
        tasks,
      );

      const managerOptions = result.filter((o) => o.optionType === EOptionTypes.Manager);

      expect(managerOptions[0].value).toBe('manager-task-1');
    });
  });
});

/// <reference types="jest" />
import { intlMock } from '../../../../../__stubs__/intlMock';
import { ETaskPerformerType, ITemplateTask } from '../../../../../types/template';
import { getPerformersForDropdown } from '../getPerformersForDropdown';
import { EOptionTypes } from '../../../../UI/form/UsersDropdown';

jest.mock('../../../../../utils/users', () => ({
  getUserFullName: jest.fn((u: any) => `${u.firstName} ${u.lastName}`),
}));

describe('getPerformersForDropdown', () => {
  const t = (id: string, values?: Record<string, string>) => intlMock.formatMessage({ id }, values);
  const MANAGER_LABEL = (step: string) => t('tasks.task-manager-of-step', { step });

  const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
    apiName: 'task-1',
    number: 1,
    name: 'First Step',
    description: '',
    delay: null,
    rawDueDate: null as any,
    requireCompletionByAll: false,
    skipForStarter: false,
    rawPerformers: [],
    fields: [],
    uuid: 'uuid-1',
    conditions: [],
    checklists: [],
    revertTask: null,
    ancestors: [],
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

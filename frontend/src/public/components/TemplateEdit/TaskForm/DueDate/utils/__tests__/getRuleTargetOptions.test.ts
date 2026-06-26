import { EExtraFieldType, IFieldsetData, IKickoffClient, ITemplateTaskClient } from '../../../../../../types/template';
import { makeExtraField } from '../../../../../../__stubs__/fields.factory';
import { makeFieldsetData, makeFieldsetBindingClient } from '../../../../../../__stubs__/fieldsets.factory';
import { createEmptyTaskDueDate } from '../../../../../../utils/dueDate/createEmptyTaskDueDate';
import { getRuleTargetOptions } from '../getRuleTargetOptions';

jest.mock('../../../../../UI', () => ({
  DropdownList: jest.fn(() => null),
}));

const makeTask = (overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient => ({
  id: 1,
  apiName: 'task-1',
  name: 'Task 1',
  description: '',
  number: 1,
  rawPerformers: [],
  requireCompletionByAll: false,
  skipForStarter: false,
  fields: [],
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  conditions: [],
  uuid: 'uuid-1',
  checklists: [],
  revertTask: null,
  ancestors: [],
  fieldsets: [],
  ...overrides,
});

const makeKickoff = (overrides: Partial<IKickoffClient> = {}): IKickoffClient => ({
  description: '',
  fields: [],
  fieldsets: [],
  ...overrides,
});


describe('getRuleTargetOptions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns 2 system rules (workflow started, task started) even without fieldsets', () => {
    const currentTask = makeTask();
    const [systemRules, dateFieldsRules, tasksRules] = getRuleTargetOptions(
      currentTask,
      [currentTask],
      makeKickoff(),
    );

    expect(systemRules).toHaveLength(2);
    expect(systemRules.find((r) => r.ruleTarget === 'workflow started')).toBeDefined();
    expect(systemRules.find((r) => r.ruleTarget === 'task started')).toBeDefined();
    expect(dateFieldsRules).toHaveLength(0);
    expect(tasksRules).toHaveLength(0);
  });

  it('only Date fields from kickoff fieldset appear in dateFieldsRules, String fields are filtered out', () => {
    const fieldsetApiName = 'fs-kickoff';

    const fieldsetData = makeFieldsetData({
      apiName: fieldsetApiName,
      fields: [
        makeExtraField({ apiName: 'date-field', name: 'Date Field', type: EExtraFieldType.Date }),
        makeExtraField({ apiName: 'string-field', name: 'String Field', order: 1 }),
      ],
    });

    const kickoff = makeKickoff({
      fieldsets: [makeFieldsetBindingClient({ apiNameBinding: fieldsetApiName })],
    });

    const fieldsetsByApiName = new Map<string, IFieldsetData>([
      [fieldsetApiName, fieldsetData],
    ]);

    const currentTask = makeTask();
    const [systemRules, dateFieldsRules] = getRuleTargetOptions(
      currentTask,
      [currentTask],
      kickoff,
      fieldsetsByApiName,
    );

    expect(systemRules).toHaveLength(2);

    expect(dateFieldsRules).toHaveLength(1);
    const dateRule = dateFieldsRules.find((r) => r.sourceId === 'date-field');
    expect(dateRule).toBeDefined();
    expect(dateRule?.ruleTarget).toBe('field');

    const stringInRules = dateFieldsRules.find((r) => r.sourceId === 'string-field');
    expect(stringInRules).toBeUndefined();
  });
});

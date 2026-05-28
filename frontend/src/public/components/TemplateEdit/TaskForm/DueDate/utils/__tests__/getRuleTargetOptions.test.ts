import { EExtraFieldType, IFieldsetData, IKickoff, ITemplateTask } from '../../../../../../types/template';
import { EFieldLabelPosition } from '../../../../../../types/fieldset';
import { createEmptyTaskDueDate } from '../../../../../../utils/dueDate/createEmptyTaskDueDate';
import { getRuleTargetOptions } from '../getRuleTargetOptions';

jest.mock('../../../../../UI', () => ({
  DropdownList: jest.fn(() => null),
}));

const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
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

const makeKickoff = (overrides: Partial<IKickoff> = {}): IKickoff => ({
  description: '',
  fields: [],
  fieldsets: [],
  ...overrides,
});

const makeFieldsetData = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Fieldset 1',
  description: '',
  order: 0,
  fields: [],
  labelPosition: EFieldLabelPosition.Top,
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
        {
          apiName: 'date-field',
          name: 'Date Field',
          type: EExtraFieldType.Date,
          order: 0,
          isRequired: false,
          isHidden: false,
          userId: null,
          groupId: null,
          description: '',
          selections: [],
        },
        {
          apiName: 'string-field',
          name: 'String Field',
          type: EExtraFieldType.String,
          order: 1,
          isRequired: false,
          isHidden: false,
          userId: null,
          groupId: null,
          description: '',
          selections: [],
        },
      ],
    });

    const kickoff = makeKickoff({
      fieldsets: [{ apiName: fieldsetApiName, order: 0 }],
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

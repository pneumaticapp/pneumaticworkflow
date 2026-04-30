import { EExtraFieldType, IFieldsetData, IKickoff, ITemplateTask } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { TTaskVariable } from '../../../types';
import {
  getKickoffVariables,
  getTaskVariables,
  getSystemVariables,
  getVariables,
  getSingleLineVariables,
  isSystemVariable,
  WORKFLOW_STARTER_VARIABLE_API_NAME,
  WORKFLOW_STARTER_VARIABLE_TITLE,
  SYSTEM_VARIABLE_SUBTITLE,
} from '../getTaskVariables';

const mockKikoff: IKickoff = {
  description: 'Kickoff description',
  fields: [
    {
      name: 'Client name',
      type: EExtraFieldType.String,
      isRequired: false,
      description: 'Enter client name',
      apiName: 'client-name-3967',
      selections: [],
      order: 1,
      userId: null,
      groupId: null,
    },
  ],
  fieldsets: [],
};

const mockTask1: ITemplateTask = {
  id: 3048,
  apiName: 'task-1',
  name: 'Task 1',
  description: "Check data on correct. If it's not - requesting for actualisation to user.",
  number: 1,
  rawPerformers: [],
  requireCompletionByAll: true,
  skipForStarter: false,
  fields: [
    {
      name: 'Large Text Field',
      type: EExtraFieldType.Text,
      isRequired: false,
      description: '',
      apiName: 'large-text-field-8622',
      selections: [],
      order: 0,
      userId: null,
      groupId: null,
    },
  ],
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  conditions: [],
  uuid: '5f6cbe6b-238e-462e-8f18-d5ee5ec45de3',
  checklists: [],
  revertTask: null,
  ancestors: [],
  fieldsets: [],
};

const mockTask2: ITemplateTask = {
  id: 3049,
  apiName: 'task-2',
  name: 'Task2',
  description: 'Checking is request actual, and that occurence repeating',
  number: 2,
  rawPerformers: [],
  requireCompletionByAll: false,
  skipForStarter: false,
  fields: [
    {
      name: 'Reasons',
      type: EExtraFieldType.Text,
      isRequired: true,
      description: 'Enter reasons of client requesting',
      apiName: 'reasons-3969',
      selections: [],
      order: 0,
      userId: null,
      groupId: null,
    },
  ],
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  conditions: [],
  uuid: '86b7e716-3819-4b2b-b306-749e0ac2f4e9',
  checklists: [],
  revertTask: null,
  ancestors: ['task-1'],
  fieldsets: [],
};

const mockFieldsetData: IFieldsetData = {
  id: 99,
  apiName: 'fs-99',
  name: 'Extra Set',
  description: '',
  fields: [
    {
      name: 'Assignee',
      type: EExtraFieldType.User,
      isRequired: false,
      description: '',
      apiName: 'assignee-fs',
      selections: [],
      order: 0,
      userId: null,
      groupId: null,
    },
    {
      name: 'Kickoff date',
      type: EExtraFieldType.Date,
      isRequired: false,
      description: '',
      apiName: 'kickoff-date-fs',
      selections: [],
      order: 1,
      userId: null,
      groupId: null,
    },
  ],
};

const mockFieldsetsById = new Map<string, IFieldsetData>([[mockFieldsetData.apiName, mockFieldsetData]]);

describe('getTaskVariables', () => {
  it("correctly gets 1st task's variables", () => {
    const tasks: ITemplateTask[] = [mockTask1, mockTask2];
    const expectedFirstTaskVariables: TTaskVariable[] = [
      {
        apiName: 'client-name-3967',
        title: 'Client name',
        subtitle: 'Kick-off form',
        richSubtitle: 'Kick-off form',
        selections: [],
        type: EExtraFieldType.String,
      },
    ];

    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask1);
    const expectedResult = expectedFirstTaskVariables;

    expect(actualResult).toStrictEqual(expectedResult);
  });

  it("correctly gets 2nd task's variables", () => {
    const tasks: ITemplateTask[] = [mockTask1, mockTask2];
    const expectedSecondTaskVariables: TTaskVariable[] = [
      {
        apiName: 'client-name-3967',
        title: 'Client name',
        subtitle: 'Kick-off form',
        richSubtitle: 'Kick-off form',
        selections: [],
        type: EExtraFieldType.String,
      },
      {
        apiName: 'large-text-field-8622',
        title: 'Large Text Field',
        subtitle: 'Task 1',
        richSubtitle: 'Task 1',
        selections: [],
        type: EExtraFieldType.Text,
      },
    ];

    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask2);
    const expectedResult = expectedSecondTaskVariables;

    expect(actualResult).toStrictEqual(expectedResult);
  });

  it('appends variables from selected task fieldsets with combined subtitles', () => {
    const taskWithFieldset: ITemplateTask = {
      ...mockTask1,
      fieldsets: [{ apiName: mockFieldsetData.apiName, order: 0 }],
    };
    const tasks: ITemplateTask[] = [taskWithFieldset, mockTask2];
    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask2, undefined, mockFieldsetsById);

    expect(actualResult.map((v) => v.apiName)).toEqual([
      'client-name-3967',
      'large-text-field-8622',
      'assignee-fs',
      'kickoff-date-fs',
    ]);
    expect(actualResult.find((v) => v.apiName === 'assignee-fs')).toMatchObject({
      title: 'Assignee',
      subtitle: 'Task 1 · Extra Set',
      type: EExtraFieldType.User,
    });
  });
});

describe('getKickoffVariables with fieldsets', () => {
  it('adds kickoff fieldset fields after regular kickoff fields', () => {
    const kickoff: IKickoff = {
      ...mockKikoff,
      fieldsets: [{ apiName: mockFieldsetData.apiName, order: 0 }],
    };
    const vars = getKickoffVariables(kickoff, mockFieldsetsById);

    expect(vars.map((v) => v.apiName)).toEqual(['client-name-3967', 'assignee-fs', 'kickoff-date-fs']);
    expect(vars[1]).toMatchObject({
      subtitle: 'Kick-off form · Extra Set',
      title: 'Assignee',
      type: EExtraFieldType.User,
    });
  });
});

describe('getSystemVariables', () => {
  it('returns array with workflow-starter variable', () => {
    const result = getSystemVariables();

    expect(result).toEqual([
      {
        apiName: WORKFLOW_STARTER_VARIABLE_API_NAME,
        title: WORKFLOW_STARTER_VARIABLE_TITLE,
        subtitle: SYSTEM_VARIABLE_SUBTITLE,
        type: EExtraFieldType.String,
      },
    ]);
  });
});

describe('isSystemVariable', () => {
  it('returns true for workflow-starter', () => {
    expect(isSystemVariable(WORKFLOW_STARTER_VARIABLE_API_NAME)).toBe(true);
  });

  it('returns false for a regular field apiName', () => {
    expect(isSystemVariable('client-name-3967')).toBe(false);
  });

  it('returns false for an empty string', () => {
    expect(isSystemVariable('')).toBe(false);
  });
});

describe('getVariables', () => {
  it('returns system variables first, then field variables', () => {
    const result = getVariables({ kickoff: mockKikoff, tasks: [] });

    expect(result[0].apiName).toBe(WORKFLOW_STARTER_VARIABLE_API_NAME);
    expect(result[1].apiName).toBe('client-name-3967');
  });

  it('includes both system and kickoff variables', () => {
    const result = getVariables({ kickoff: mockKikoff, tasks: [] });

    expect(result).toHaveLength(2);
  });

  it('returns only system variables when no kickoff or tasks provided', () => {
    const result = getVariables({});

    expect(result).toHaveLength(1);
    expect(result[0].apiName).toBe(WORKFLOW_STARTER_VARIABLE_API_NAME);
  });
});

describe('getSingleLineVariables', () => {
  it('includes String type variables (like workflow-starter)', () => {
    const variables: TTaskVariable[] = [
      {
        apiName: WORKFLOW_STARTER_VARIABLE_API_NAME,
        title: WORKFLOW_STARTER_VARIABLE_TITLE,
        type: EExtraFieldType.String,
      },
      {
        apiName: 'text-field',
        title: 'Text',
        type: EExtraFieldType.Text,
      },
    ];

    const result = getSingleLineVariables(variables);

    expect(result).toHaveLength(1);
    expect(result[0].apiName).toBe(WORKFLOW_STARTER_VARIABLE_API_NAME);
  });

  it('filters out multi-line types (Text, File, Url)', () => {
    const variables: TTaskVariable[] = [
      { apiName: 'text', title: 'Text', type: EExtraFieldType.Text },
      { apiName: 'file', title: 'File', type: EExtraFieldType.File },
      { apiName: 'url', title: 'Url', type: EExtraFieldType.Url },
    ];

    expect(getSingleLineVariables(variables)).toHaveLength(0);
  });

  it('keeps Number, Date, User, Radio, Checkbox, Creatable types', () => {
    const variables: TTaskVariable[] = [
      { apiName: 'num', title: 'Num', type: EExtraFieldType.Number },
      { apiName: 'date', title: 'Date', type: EExtraFieldType.Date },
      { apiName: 'user', title: 'User', type: EExtraFieldType.User },
      { apiName: 'radio', title: 'Radio', type: EExtraFieldType.Radio },
      { apiName: 'check', title: 'Check', type: EExtraFieldType.Checkbox },
      { apiName: 'drop', title: 'Drop', type: EExtraFieldType.Creatable },
    ];

    expect(getSingleLineVariables(variables)).toHaveLength(6);
  });
});

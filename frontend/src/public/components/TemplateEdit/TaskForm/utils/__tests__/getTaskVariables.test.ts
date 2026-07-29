import { createElement } from 'react';
import { render, screen } from '@testing-library/react';

import { EExtraFieldType, IKickoffClient, ITemplateTaskClient } from '../../../../../types/template';
import { IFieldsetRuntime } from '../../../../../types/fieldset';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { makeFieldsetRuntime, makeFieldsetBindingClient, makeFieldsetField } from '../../../../../__stubs__/fieldsets.factory';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { TTaskVariable } from '../../../types';
import {
  getKickoffVariables,
  getTaskVariables,
  getSystemVariables,
  getVariables,
  getSingleLineVariables,
  isSystemVariable,
  useWorkflowNameVariables,
  WORKFLOW_STARTER_VARIABLE_API_NAME,
  WORKFLOW_STARTER_VARIABLE_TITLE,
  SYSTEM_VARIABLE_SUBTITLE,
} from '../getTaskVariables';

const mockKikoff: IKickoffClient = {
  description: 'Kickoff description',
  fields: [
    makeExtraField({
      name: 'Client name',
      description: 'Enter client name',
      apiName: 'client-name-3967',
      order: 1,
    }),
  ],
  fieldsets: [],
};

const mockTask1: ITemplateTaskClient = {
  id: 3048,
  apiName: 'task-1',
  name: 'Task 1',
  description: "Check data on correct. If it's not - requesting for actualisation to user.",
  number: 1,
  rawPerformers: [],
  requireCompletionByAll: true,
  skipForStarter: false,
  fields: [
    makeExtraField({
      name: 'Large Text Field',
      type: EExtraFieldType.Text,
      apiName: 'large-text-field-8622',
    }),
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

const mockTask2: ITemplateTaskClient = {
  id: 3049,
  apiName: 'task-2',
  name: 'Task2',
  description: 'Checking is request actual, and that occurence repeating',
  number: 2,
  rawPerformers: [],
  requireCompletionByAll: false,
  skipForStarter: false,
  fields: [
    makeExtraField({
      name: 'Reasons',
      type: EExtraFieldType.Text,
      isRequired: true,
      description: 'Enter reasons of client requesting',
      apiName: 'reasons-3969',
    }),
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

const mockFieldsetData: IFieldsetRuntime = makeFieldsetRuntime({
  apiNameBinding: 'fs-99',
  name: 'Extra Set',
  fields: [
    makeExtraField({
      name: 'Assignee',
      type: EExtraFieldType.User,
      apiName: 'assignee-fs',
    }),
    makeExtraField({
      name: 'Kickoff date',
      type: EExtraFieldType.Date,
      apiName: 'kickoff-date-fs',
      order: 1,
    }),
  ],
});

const mockBindingFields = [
  makeFieldsetField({
    name: 'Assignee',
    type: EExtraFieldType.User,
    apiName: 'assignee-fs',
  }),
  makeFieldsetField({
    name: 'Kickoff date',
    type: EExtraFieldType.Date,
    apiName: 'kickoff-date-fs',
    order: 1,
  }),
];


describe('getTaskVariables', () => {
  it("correctly gets 1st task's variables", () => {
    const tasks: ITemplateTaskClient[] = [mockTask1, mockTask2];
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
    const tasks: ITemplateTaskClient[] = [mockTask1, mockTask2];
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
    const taskWithFieldset: ITemplateTaskClient = {
      ...mockTask1,
      fieldsets: [makeFieldsetBindingClient({
        apiNameBinding: mockFieldsetData.apiNameBinding,
        name: mockFieldsetData.name,
        fields: mockBindingFields,
      })],
    };
    const tasks: ITemplateTaskClient[] = [taskWithFieldset, mockTask2];
    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask2);

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

  it('expands task-fieldset with inline `fields` without using the catalog', () => {
    const inlineFieldset = makeFieldsetBindingClient({
      apiNameBinding: 'fs-inline',
      name: 'Inline Set',
      fields: [
        makeFieldsetField({
          apiName: 'inline-field-1',
          name: 'Inline Field',
        }),
      ],
    });
    const taskWithInline: ITemplateTaskClient = {
      ...mockTask1,
      fieldsets: [inlineFieldset],
    };
    const tasks: ITemplateTaskClient[] = [taskWithInline, mockTask2];

    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask2);

    const inlineVar = actualResult.find((v) => v.apiName === 'inline-field-1');
    expect(inlineVar).toBeDefined();
    expect(inlineVar).toMatchObject({
      title: 'Inline Field',
      subtitle: 'Task 1 · Inline Set',
      type: EExtraFieldType.String,
    });
  });
});

describe('getKickoffVariables with fieldsets', () => {
  it('adds kickoff fieldset fields after regular kickoff fields', () => {
    const kickoff: IKickoffClient = {
      ...mockKikoff,
      fieldsets: [makeFieldsetBindingClient({
        apiNameBinding: mockFieldsetData.apiNameBinding,
        name: mockFieldsetData.name,
        fields: mockBindingFields,
      })],
    };
    const vars = getKickoffVariables(kickoff);

    expect(vars.map((v) => v.apiName)).toEqual(['client-name-3967', 'assignee-fs', 'kickoff-date-fs']);
    expect(vars[1]).toMatchObject({
      subtitle: 'Kick-off form · Extra Set',
      title: 'Assignee',
      type: EExtraFieldType.User,
    });
  });

  it('skips fieldset missing from catalog without crashing or producing phantom options', () => {
    const kickoff: IKickoffClient = {
      ...mockKikoff,
      fieldsets: [
        makeFieldsetBindingClient({ apiNameBinding: 'missing-fs' }),
        makeFieldsetBindingClient({
          apiNameBinding: mockFieldsetData.apiNameBinding,
          name: mockFieldsetData.name,
          fields: mockBindingFields,
          order: 1,
        }),
      ],
    };

    const vars = getKickoffVariables(kickoff);

    expect(vars.map((v) => v.apiName)).toEqual(['client-name-3967', 'assignee-fs', 'kickoff-date-fs']);
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

  it('returns only system variables when kickoff and tasks are empty', () => {
    const result = getVariables({ kickoff: { fields: [], fieldsets: [] }, tasks: [] });

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

describe('useWorkflowNameVariables', () => {
  function TestWrapper({
    kickoff,
  }: {
    kickoff?: Parameters<typeof useWorkflowNameVariables>[0];
  }) {
    const vars = useWorkflowNameVariables(kickoff);
    return createElement(
      'div',
      null,
      vars.map((v) =>
        createElement(
          'span',
          { key: v.apiName, 'data-testid': `var-${v.apiName}`, 'data-type': v.type },
          v.title,
        ),
      ),
    );
  }

  it('includes 4 system variables plus single-line kickoff and fieldset fields, filters out multi-line types', () => {

    const kickoff: IKickoffClient = {
      description: '',
      fields: [
        makeExtraField({
          apiName: 'kickoff-string',
          name: 'Kickoff String',
        }),
        makeExtraField({
          apiName: 'kickoff-text',
          name: 'Kickoff Text',
          type: EExtraFieldType.Text,
          order: 1,
        }),
      ],
      fieldsets: [makeFieldsetBindingClient({
        apiNameBinding: 'fs-name',
        fields: [
          makeFieldsetField({
            apiName: 'fs-date',
            name: 'FS Date',
            type: EExtraFieldType.Date,
          }),
          makeFieldsetField({
            apiName: 'fs-number',
            name: 'FS Number',
            type: EExtraFieldType.Number,
            order: 1,
          }),
          makeFieldsetField({
            apiName: 'fs-text',
            name: 'FS Text',
            type: EExtraFieldType.Text,
            order: 2,
          }),
        ],
      })],
    };

    render(createElement(TestWrapper, { kickoff }));

    expect(screen.getByTestId('var-date')).toBeInTheDocument();
    expect(screen.getByTestId('var-template-name')).toBeInTheDocument();
    expect(screen.getByTestId('var-workflow-id')).toBeInTheDocument();
    expect(screen.getByTestId('var-workflow-starter')).toBeInTheDocument();

    expect(screen.getByTestId('var-kickoff-string')).toBeInTheDocument();

    expect(screen.getByTestId('var-fs-date')).toBeInTheDocument();
    expect(screen.getByTestId('var-fs-number')).toBeInTheDocument();

    expect(screen.queryByTestId('var-kickoff-text')).not.toBeInTheDocument();
    expect(screen.queryByTestId('var-fs-text')).not.toBeInTheDocument();
  });
});

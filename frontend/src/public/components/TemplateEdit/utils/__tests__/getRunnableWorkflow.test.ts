// <reference types="jest" />
import { ETaskPerformerType, EExtraFieldType, ITemplateResponse, ETemplateOwnerType, ETemplateOwnerRole } from '../../../../types/template';
import { getRunnableWorkflow } from '../getRunnableWorkflow';

const templateResponseMock: ITemplateResponse = {
  id: 4654,
  name: 'End Template',
  description: '12346789',
  tasks: [
    {
      id: 14702,
      name: 'First Step',
      number: 1,
      description: '12',
      requireCompletionByAll: false,
      skipForStarter: false,
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-059819',
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
        {
          sourceId: null,
          type: ETaskPerformerType.WorkflowStarter,
          label: 'Workflow starter',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
      ancestors: [],
      fieldsets: [],
    },
    {
      id: 14703,
      name: 'New Step 2',
      number: 2,
      description: '1233',
      requireCompletionByAll: false,
      skipForStarter: false,
      delay: null,
      rawDueDate: null,
      fields: [
        {
          id: 21478,
          type: EExtraFieldType.String,
          name: '12 21 12 12 12222222222',
          description: '',
          isRequired: false,
          order: 0,
          apiName: 'field-27fb3d',
          userId: null,
          groupId: null,
        },
      ],
      conditions: [],
      apiName: 'task-4e99a7',
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
      ancestors: ['task-059819'],
      fieldsets: [],
    },
    {
      id: 14707,
      name: 'New Step 3',
      number: 3,
      description: '',
      requireCompletionByAll: false,
      skipForStarter: false,
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-a889d4',
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
      ancestors: ['task-059819', 'task-4e99a7'],
      fieldsets: [],
    },
    {
      id: 14708,
      name: 'New Step 4',
      number: 4,
      description: '',
      requireCompletionByAll: false,
      skipForStarter: false,
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-1e9ba6',
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
      ancestors: ['task-059819', 'task-4e99a7', 'task-a889d4'],
      fieldsets: [],
    },
    {
      id: 14709,
      name: 'New Step 5',
      number: 5,
      description: '',
      requireCompletionByAll: false,
      skipForStarter: false,
      delay: null,
      dueIn: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-05a887',
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
      ancestors: ['task-059819', 'task-4e99a7', 'task-a889d4', 'task-1e9ba6'],
      fieldsets: [],
    },
  ],
  kickoff: {
    description: '',
    fields: [],
    fieldsets: [],
  },
  owners: [
    {
      sourceId: '306',
      type: ETemplateOwnerType.User,
      apiName: 'owner-024t43',
      role: ETemplateOwnerRole.Owner,
    },
    {
      sourceId: '1896',
      type: ETemplateOwnerType.User,
      apiName: 'owner-024t12',
      role: ETemplateOwnerRole.Owner,
    },
  ],
  isActive: true,
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  embedUrl: null,
  isEmbedded: false,
  finalizable: true,
  completionNotification: false,
  reminderNotification: false,
  updatedBy: 306,
  dateUpdated: '2021-10-13T14:24:43.980066Z',
  wfNameTemplate: null,
};

const stringifyReturn = {
  id: 4654,
  name: 'End Template',
  kickoff: {
    description: '',
    fields: [],
    fieldsets: [],
  },
  description: '12346789',
  performersCount: 1,
  tasksCount: 5,
  wfNameTemplate: null,
  loadedFieldsets: [],
};

describe('getRunnableWorkflow.', () => {
  it('return correct workflow data', () => {
    const runnableWorkflow = getRunnableWorkflow(templateResponseMock);

    expect(runnableWorkflow).toStrictEqual(stringifyReturn);
  });

  it('populates selections from datasetsMap when field has dataset', () => {
    const template = {
      ...templateResponseMock,
      kickoff: {
        description: '',
        fields: [
          {
            apiName: 'field-ds',
            name: 'DS Field',
            type: EExtraFieldType.Checkbox,
            order: 0,
            userId: null,
            groupId: null,
            dataset: 5,
            selections: [],
          },
        ],
        fieldsets: [],
      },
    };

    const datasetsMap = { 5: ['A', 'B'] };
    const result = getRunnableWorkflow(template, datasetsMap);

    expect(result!.kickoff.fields[0].selections).toEqual(['A', 'B']);
  });

  it('normalizes object selections into string[] when field has no dataset', () => {
    const template = {
      ...templateResponseMock,
      kickoff: {
        description: '',
        fields: [
          {
            apiName: 'field-obj',
            name: 'Obj Field',
            type: EExtraFieldType.Checkbox,
            order: 0,
            userId: null,
            groupId: null,
            selections: [{ value: 'A', apiName: 'sel-1' }, { value: 'B', apiName: 'sel-2' }],
          },
        ],
        fieldsets: [],
      },
    };

    const result = getRunnableWorkflow(template);

    expect(result!.kickoff.fields[0].selections).toEqual(['A', 'B']);
  });

  it('passes string selections as-is when field has no dataset', () => {
    const template = {
      ...templateResponseMock,
      kickoff: {
        description: '',
        fields: [
          {
            apiName: 'field-str',
            name: 'Str Field',
            type: EExtraFieldType.Checkbox,
            order: 0,
            userId: null,
            groupId: null,
            selections: ['A', 'B'],
          },
        ],
        fieldsets: [],
      },
    };

    const result = getRunnableWorkflow(template);

    expect(result!.kickoff.fields[0].selections).toEqual(['A', 'B']);
  });

  it('falls back to empty array when datasetsMap does not contain the dataset id', () => {
    const template = {
      ...templateResponseMock,
      kickoff: {
        description: '',
        fields: [
          {
            apiName: 'field-miss',
            name: 'Missing DS',
            type: EExtraFieldType.Checkbox,
            order: 0,
            userId: null,
            groupId: null,
            dataset: 99,
            selections: [],
          },
        ],
        fieldsets: [],
      },
    };

    const datasetsMap = { 5: ['X'] };
    const result = getRunnableWorkflow(template, datasetsMap);

    expect(result!.kickoff.fields[0].selections).toEqual([]);
  });

  it('returns null when isActive is false', () => {
    const template = {
      ...templateResponseMock,
      isActive: false,
    };

    const result = getRunnableWorkflow(template);

    expect(result).toBeNull();
  });
});

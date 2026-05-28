import { ETaskPerformerType, EExtraFieldType, ITemplateResponse, ETemplateOwnerType, ETemplateOwnerRole, IKickoff, IFieldsetData, IExtraField } from '../../../../types/template';
import { getRunnableWorkflow, loadFieldsetsData, loadDatasetsMap } from '../getRunnableWorkflow';
import { getFieldsets } from '../../../../api/fieldsets/getFieldsets';
import { getDataset } from '../../../../api/datasets/getDataset';

jest.mock('../../../../api/fieldsets/getFieldsets', () => ({
  getFieldsets: jest.fn(),
}));

jest.mock('../../../../api/datasets/getDataset', () => ({
  getDataset: jest.fn(),
}));

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

const assertNonNull = <T>(value: T | null, message: string): T => {
  if (value === null) {
    throw new Error(message);
  }
  return value;
};

describe('getRunnableWorkflow.', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

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
    const result = assertNonNull(getRunnableWorkflow(template, datasetsMap), 'expected non-null result');

    expect(result.kickoff.fields[0].selections).toEqual(['A', 'B']);
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

    const result = assertNonNull(getRunnableWorkflow(template), 'expected non-null result');

    expect(result.kickoff.fields[0].selections).toEqual(['A', 'B']);
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

    const result = assertNonNull(getRunnableWorkflow(template), 'expected non-null result');

    expect(result.kickoff.fields[0].selections).toEqual(['A', 'B']);
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
    const result = assertNonNull(getRunnableWorkflow(template, datasetsMap), 'expected non-null result');

    expect(result.kickoff.fields[0].selections).toEqual([]);
  });

  it('returns null when isActive is false or template id is missing', () => {
    expect(getRunnableWorkflow({ ...templateResponseMock, isActive: false })).toBeNull();

    type TRunnableInput = Parameters<typeof getRunnableWorkflow>[0];
    const { id, ...templateWithoutId } = templateResponseMock;
    expect(
      getRunnableWorkflow(templateWithoutId as unknown as TRunnableInput),
    ).toBeNull();
  });

  it('loadFieldsetsData returns [] and does not call getFieldsets when kickoff.fieldsets is empty', async () => {
    const kickoff: IKickoff = { description: '', fields: [], fieldsets: [] };

    const result = await loadFieldsetsData(kickoff, 42);

    expect(result).toEqual([]);
    expect(getFieldsets).not.toHaveBeenCalled();
  });

  it('loadFieldsetsData filters catalog by selected apiNames and inherits order from kickoff', async () => {
    const kickoff: IKickoff = {
      description: '',
      fields: [],
      fieldsets: [
        { apiName: 'fs-a', order: 5 },
        { apiName: 'fs-b', order: 10 },
      ],
    };
    (getFieldsets as jest.Mock).mockResolvedValue({
      results: [
        { id: 1, apiName: 'fs-a', name: 'A', fields: [], order: 0 },
        { id: 2, apiName: 'fs-b', name: 'B', fields: [], order: 0 },
        { id: 3, apiName: 'fs-c', name: 'C', fields: [], order: 0 },
      ],
    });

    const result = await loadFieldsetsData(kickoff, 42);

    expect(result.length).toBe(2);
    const byApiName = Object.fromEntries(result.map((fs) => [fs.apiName, fs.order]));
    expect(byApiName['fs-a']).toBe(5);
    expect(byApiName['fs-b']).toBe(10);
    expect(result.find((fs) => fs.apiName === 'fs-c')).toBeUndefined();
  });

  it('loadDatasetsMap returns {} and does not call getDataset when there are no dataset ids', async () => {
    const kickoff: IKickoff = { description: '', fields: [], fieldsets: [] };

    const result = await loadDatasetsMap(kickoff, []);

    expect(result).toEqual({});
    expect(getDataset).not.toHaveBeenCalled();
  });

  it('loadDatasetsMap dedups dataset id shared by a kickoff field and a fieldset field', async () => {
    const makeFieldWithDataset = (apiName: string, name: string, datasetId: number): IExtraField => ({
      apiName,
      name,
      type: EExtraFieldType.Checkbox,
      order: 0,
      isRequired: false,
      dataset: datasetId,
      selections: [],
      userId: null,
      groupId: null,
    });
    const kickoff: IKickoff = {
      description: '',
      fields: [makeFieldWithDataset('k-f', 'K', 7)],
      fieldsets: [],
    };
    const fieldsets: IFieldsetData[] = [
      {
        id: 1,
        apiName: 'fs-1',
        name: 'FS',
        description: '',
        order: 0,
        fields: [makeFieldWithDataset('fs-f', 'F', 7)],
      },
    ];
    (getDataset as jest.Mock).mockResolvedValue({ items: [{ value: 'A' }, { value: 'B' }] });

    const result = await loadDatasetsMap(kickoff, fieldsets);

    expect(getDataset).toHaveBeenCalledTimes(1);
    expect(getDataset).toHaveBeenCalledWith({ id: 7 });
    expect(result).toEqual({ 7: ['A', 'B'] });
  });

  it('getRunnableWorkflow applies datasetsMap and normalizes selections for fieldset fields', () => {
    const datasetsMap = { 5: ['X', 'Y'] };
    const fieldWithDataset: IExtraField = {
      apiName: 'fs-f-ds',
      name: 'DS',
      type: EExtraFieldType.Checkbox,
      order: 0,
      isRequired: false,
      dataset: 5,
      selections: [],
      userId: null,
      groupId: null,
    };
    const fieldWithObjectSelections: IExtraField = {
      apiName: 'fs-f-obj',
      name: 'Obj',
      type: EExtraFieldType.Checkbox,
      order: 1,
      isRequired: false,
      selections: [
        { value: 'P', apiName: 's-1' },
        { value: 'Q', apiName: 's-2' },
      ],
      userId: null,
      groupId: null,
    };
    const loadedFieldsets: IFieldsetData[] = [
      {
        id: 1,
        apiName: 'fs-1',
        name: 'FS',
        description: '',
        order: 0,
        fields: [fieldWithDataset, fieldWithObjectSelections],
      },
    ];

    const result = assertNonNull(
      getRunnableWorkflow(templateResponseMock, datasetsMap, loadedFieldsets),
      'expected non-null result',
    );
    const { loadedFieldsets: loaded } = result;
    if (loaded === undefined) {
      throw new Error('expected loadedFieldsets to be defined');
    }
    expect(loaded).toHaveLength(1);
    expect(loaded[0].fields[0].selections).toEqual(['X', 'Y']);
    expect(loaded[0].fields[1].selections).toEqual(['P', 'Q']);
  });
});

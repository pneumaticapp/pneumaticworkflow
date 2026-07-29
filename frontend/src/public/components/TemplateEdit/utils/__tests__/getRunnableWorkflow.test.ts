import { ETaskPerformerType, EExtraFieldType, IKickoffClient } from '../../../../types/template';
import { IFieldsetRuntime } from '../../../../types/fieldset';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../../__stubs__/fieldsets.factory';
import { getRunnableWorkflow, loadDatasetsMap, TTemplateToRunWorkflow } from '../getRunnableWorkflow';
import { getDataset } from '../../../../api/datasets/getDataset';

jest.mock('../../../../api/datasets/getDataset', () => ({
  getDataset: jest.fn(),
}));

const templateResponseMock: TTemplateToRunWorkflow = {
  id: 4654,
  name: 'End Template',
  description: '12346789',
  tasks: [
    {
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
    },
    {
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
    },
    {
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
    },
    {
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
    },
    {
      rawPerformers: [
        {
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
    },
  ],
  kickoff: {
    description: '',
    fields: [],
    fieldsets: [],
  },
  isActive: true,
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
          makeExtraField({ apiName: 'field-ds', name: 'DS Field', type: EExtraFieldType.Checkbox, dataset: 5 }),
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
          makeExtraField({
            apiName: 'field-obj',
            name: 'Obj Field',
            type: EExtraFieldType.Checkbox,
            selections: [{ value: 'A', apiName: 'sel-1' }, { value: 'B', apiName: 'sel-2' }],
          }),
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
          makeExtraField({ apiName: 'field-str', name: 'Str Field', type: EExtraFieldType.Checkbox, selections: ['A', 'B'] }),
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
          makeExtraField({ apiName: 'field-miss', name: 'Missing DS', type: EExtraFieldType.Checkbox, dataset: 99 }),
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


  it('loadDatasetsMap returns {} and does not call getDataset when there are no dataset ids', async () => {
    const kickoff: IKickoffClient = { description: '', fields: [], fieldsets: [] };

    const result = await loadDatasetsMap(kickoff, []);

    expect(result).toEqual({});
    expect(getDataset).not.toHaveBeenCalled();
  });

  it('loadDatasetsMap dedups dataset id shared by a kickoff field and a fieldset field', async () => {
    const kickoff: IKickoffClient = {
      description: '',
      fields: [makeExtraField({ apiName: 'k-f', name: 'K', type: EExtraFieldType.Checkbox, dataset: 7 })],
      fieldsets: [],
    };
    const fieldsets: IFieldsetRuntime[] = [
      makeFieldsetRuntime({
        name: 'FS',
        fields: [makeExtraField({ apiName: 'fs-f', name: 'F', type: EExtraFieldType.Checkbox, dataset: 7 })],
      }),
    ];
    (getDataset as jest.Mock).mockResolvedValue({ items: [{ value: 'A' }, { value: 'B' }] });

    const result = await loadDatasetsMap(kickoff, fieldsets);

    expect(getDataset).toHaveBeenCalledTimes(1);
    expect(getDataset).toHaveBeenCalledWith({ id: 7 });
    expect(result).toEqual({ 7: ['A', 'B'] });
  });

  it('getRunnableWorkflow applies datasetsMap and normalizes selections for fieldset fields', () => {
    const datasetsMap = { 5: ['X', 'Y'] };
    const fieldWithDataset = makeExtraField({
      apiName: 'fs-f-ds',
      name: 'DS',
      type: EExtraFieldType.Checkbox,
      dataset: 5,
    });
    const fieldWithObjectSelections = makeExtraField({
      apiName: 'fs-f-obj',
      name: 'Obj',
      type: EExtraFieldType.Checkbox,
      order: 1,
      selections: [
        { value: 'P', apiName: 's-1' },
        { value: 'Q', apiName: 's-2' },
      ],
    });
    const loadedFieldsets: IFieldsetRuntime[] = [
      makeFieldsetRuntime({ name: 'FS', fields: [fieldWithDataset, fieldWithObjectSelections] }),
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

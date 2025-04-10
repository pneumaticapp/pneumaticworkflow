import { ETaskPerformerType, EExtraFieldType, ITemplateResponse, ETemplateOwnerType } from '../../../../types/template';
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
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-059819',
      rawPerformers: [
        {
          id: 10057,
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
        {
          id: 10060,
          sourceId: null,
          type: ETaskPerformerType.WorkflowStarter,
          label: 'Workflow starter',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
    },
    {
      id: 14703,
      name: 'New Step 2',
      number: 2,
      description: '1233',
      requireCompletionByAll: false,
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
        },
      ],
      conditions: [],
      apiName: 'task-4e99a7',
      rawPerformers: [
        {
          id: 10058,
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
    },
    {
      id: 14707,
      name: 'New Step 3',
      number: 3,
      description: '',
      requireCompletionByAll: false,
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-a889d4',
      rawPerformers: [
        {
          id: 10066,
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
    },
    {
      id: 14708,
      name: 'New Step 4',
      number: 4,
      description: '',
      requireCompletionByAll: false,
      delay: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-1e9ba6',
      rawPerformers: [
        {
          id: 10067,
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
    },
    {
      id: 14709,
      name: 'New Step 5',
      number: 5,
      description: '',
      requireCompletionByAll: false,
      delay: null,
      dueIn: null,
      rawDueDate: null,
      fields: [],
      conditions: [],
      apiName: 'task-05a887',
      rawPerformers: [
        {
          id: 10068,
          sourceId: '306',
          type: ETaskPerformerType.User,
          label: 'Yevgeniy Tsymbalyuk',
          apiName: 'raw-performer-024t43',
        },
      ],
      checklists: [],
      revertTask: null,
    },
  ],
  kickoff: {
    description: '',
    fields: [],
  },
  owners: [
    {
      sourceId: '306',
      type: ETemplateOwnerType.User,
      apiName: 'owner-024t43',
    },
    {
      sourceId: '1896',
      type: ETemplateOwnerType.User,
      apiName: 'owner-024t12',
    },
  ],
  isActive: true,
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  embedUrl: null,
  isEmbedded: false,
  finalizable: true,
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
  },
  description: '12346789',
  performersCount: 1,
  tasksCount: 5,
  wfNameTemplate: null,
};

describe('getRunnableWorkflow.', () => {
  it('return correct workflow data', () => {
    const runnableWorkflow = getRunnableWorkflow(templateResponseMock);

    expect(runnableWorkflow).toStrictEqual(stringifyReturn);
  });
});

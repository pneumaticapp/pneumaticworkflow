import {
  buildWorkflowsCsvContent,
  downloadWorkflowsCsv,
  IExportWorkflowsToCsvConfig,
} from '../exportWorkflowsToCsv';
import { IWorkflowClient } from '../../../types/workflow';
import { ITableViewFields } from '../../../types/template';
import { ETemplateOwnerType } from '../../../types/template';
import { EExtraFieldType } from '../../../types/template';

const minimalWorkflow = (
  overrides: Partial<IWorkflowClient> = {},
): IWorkflowClient =>
  ({
    id: 1,
    name: 'Workflow One',
    workflowStarter: 100,
    isExternal: false,
    template: { id: 10, name: 'Template A', isActive: true, wfNameTemplate: null },
    completedTasks: [],
    tasksCountWithoutSkipped: 2,
    areMultipleTasks: false,
    oneActiveTaskName: 'Step 1',
    selectedUsers: [{ type: ETemplateOwnerType.User, sourceId: 200 }],
    fields: [],
    ...overrides,
  }) as IWorkflowClient;

const systemHeaderLabels: Record<string, string> = {
  'system-column-workflow': 'Workflow',
  'system-column-templateName': 'Template',
  'system-column-starter': 'Starter',
  'system-column-progress': 'Progress',
  'system-column-step': 'Step',
  'system-column-performer': 'Performer',
};

describe('exportWorkflowsToCsv', () => {
  describe('buildWorkflowsCsvContent', () => {
    const baseConfig: IExportWorkflowsToCsvConfig = {
      workflows: [],
      users: [],
      groups: [],
      selectedFields: [],
      headerLabels: { ...systemHeaderLabels },
      deletedGroupFallbackTemplate: 'Deleted Group (ID: {id})',
    };

    it('returns only header row when workflows array is empty', () => {
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        selectedFields: [
          'system-column-workflow',
          'system-column-templateName',
          'system-column-starter',
          'system-column-progress',
          'system-column-step',
          'system-column-performer',
        ],
        headerLabels: systemHeaderLabels,
      });
      const lines = result.split('\r\n');
      expect(lines).toHaveLength(1);
      expect(lines[0]).toBe(
        'Workflow,Template,Starter,Progress,Step,Performer',
      );
    });

    it('uses default system columns when selectedFields is empty and no optional fields', () => {
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        selectedFields: [],
        optionalFieldsFromWorkflow: [],
        headerLabels: systemHeaderLabels,
      });
      expect(result).toContain('Workflow,Template,Starter,Progress,Step,Performer');
    });

    it('outputs one data row for one workflow with system columns', () => {
      const workflows = [
        minimalWorkflow({
          name: 'My Process',
          template: { id: 1, name: 'T1', isActive: true, wfNameTemplate: null },
          workflowStarter: 1,
          completedTasks: [{ id: 1 } as never],
          tasksCountWithoutSkipped: 2,
          areMultipleTasks: false,
          oneActiveTaskName: 'Task A',
          selectedUsers: [],
        }),
      ];
      const users = [{ id: 1, firstName: 'Alice', lastName: 'Smith', email: '' } as never];
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        workflows,
        users,
        selectedFields: [
          'system-column-workflow',
          'system-column-templateName',
          'system-column-starter',
          'system-column-progress',
          'system-column-step',
          'system-column-performer',
        ],
        headerLabels: systemHeaderLabels,
      });
      const lines = result.split('\r\n');
      expect(lines).toHaveLength(2);
      expect(lines[0]).toBe(
        'Workflow,Template,Starter,Progress,Step,Performer',
      );
      expect(lines[1]).toContain('My Process');
      expect(lines[1]).toContain('T1');
      expect(lines[1]).toContain('Alice Smith');
      expect(lines[1]).toContain('50%');
      expect(lines[1]).toContain('Task A');
    });

    it('escapes CSV cells containing comma and double quote', () => {
      const workflows = [
        minimalWorkflow({ name: 'Name with "quotes" and, comma' }),
      ];
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        workflows,
        selectedFields: ['system-column-workflow'],
        headerLabels: { 'system-column-workflow': 'Name' },
      });
      expect(result).toContain('"Name with ""quotes"" and, comma"');
    });

    it('includes optional fields when provided and in selectedFields', () => {
      const optionalFields: ITableViewFields[] = [
        {
          id: 1,
          apiName: 'field-custom',
          name: 'Custom',
          type: EExtraFieldType.String,
          order: 0,
          taskId: null,
          kickoffId: null,
          markdownValue: '',
          clearValue: 'Custom value',
          userId: 0,
          groupId: 0,
          value: 'Custom value',
        } as unknown as ITableViewFields,
      ];
      const workflows = [
        minimalWorkflow({
          fields: [
            {
              ...optionalFields[0],
              clearValue: 'Custom value',
              value: 'Custom value',
            } as unknown as ITableViewFields,
          ],
        }),
      ];
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        workflows,
        selectedFields: ['system-column-workflow', 'field-custom'],
        optionalFieldsFromWorkflow: optionalFields,
        headerLabels: {
          ...systemHeaderLabels,
          'field-custom': 'Custom',
        },
      });
      expect(result).toContain('Custom');
      expect(result).toContain('Custom value');
    });

    it('uses "Tasks" for step when areMultipleTasks is true', () => {
      const workflows = [
        minimalWorkflow({ areMultipleTasks: true, oneActiveTaskName: null }),
      ];
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        workflows,
        selectedFields: ['system-column-step'],
        headerLabels: { 'system-column-step': 'Step' },
      });
      expect(result).toContain('Tasks');
    });

    it('uses deletedGroupFallbackTemplate for performer when group is not in list', () => {
      const workflows = [
        minimalWorkflow({
          selectedUsers: [
            { type: ETemplateOwnerType.UserGroup, sourceId: 999 },
          ],
        }),
      ];
      const result = buildWorkflowsCsvContent({
        ...baseConfig,
        workflows,
        groups: [],
        selectedFields: ['system-column-performer'],
        headerLabels: { 'system-column-performer': 'Performer' },
        deletedGroupFallbackTemplate: 'Deleted Group (ID: {id})',
      });
      expect(result).toContain('Deleted Group (ID: 999)');
    });
  });

  describe('downloadWorkflowsCsv', () => {
    it('creates blob with UTF-8 BOM and csv content and triggers download', () => {
      const createObjectURL = jest.fn(() => 'blob:mock-url');
      const revokeObjectURL = jest.fn();
      const click = jest.fn();

      const originalCreateObjectURL = URL.createObjectURL;
      const originalRevokeObjectURL = URL.revokeObjectURL;
      URL.createObjectURL = createObjectURL;
      URL.revokeObjectURL = revokeObjectURL;

      const mockLink = {
        setAttribute: jest.fn(),
        style: {},
        click,
      };
      const createElement = jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
        if (tag === 'a') return mockLink as unknown as HTMLAnchorElement;
        return document.createElement(tag);
      });
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as never);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as never);

      downloadWorkflowsCsv('col1,col2\r\nv1,v2', 'export.csv');

      expect(createObjectURL).toHaveBeenCalledTimes(1);
      const callArgs = (createObjectURL as jest.Mock).mock.calls[0];
      const blob = callArgs?.[0] as Blob | undefined;
      expect(blob).toBeDefined();
      expect(blob?.type).toBe('text/csv;charset=utf-8');
      expect(blob?.size).toBeGreaterThan(0);
      expect(mockLink.setAttribute).toHaveBeenCalledWith('href', 'blob:mock-url');
      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'export.csv');
      expect(click).toHaveBeenCalled();
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');

      createElement.mockRestore();
      URL.createObjectURL = originalCreateObjectURL;
      URL.revokeObjectURL = originalRevokeObjectURL;
    });

    it('uses default filename workflows.csv when not provided', () => {
      const createObjectURL = jest.fn(() => 'blob:mock-url');
      const mockLink = { setAttribute: jest.fn(), style: {}, click: jest.fn() };
      const originalCreateObjectURL = URL.createObjectURL;
      const originalRevokeObjectURL = URL.revokeObjectURL;
      URL.createObjectURL = createObjectURL;
      URL.revokeObjectURL = jest.fn();
      jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
        if (tag === 'a') return mockLink as unknown as HTMLAnchorElement;
        return document.createElement(tag);
      });
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as never);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as never);

      downloadWorkflowsCsv('a,b');

      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'workflows.csv');

      URL.createObjectURL = originalCreateObjectURL;
      URL.revokeObjectURL = originalRevokeObjectURL;
    });
  });
});

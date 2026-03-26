jest.mock('exceljs', () => ({
  Workbook: jest.fn().mockImplementation(() => ({
    addWorksheet: jest.fn().mockReturnValue({
      addRow: jest.fn(),
    }),
    xlsx: {
      writeBuffer: jest.fn().mockResolvedValue(new Uint8Array([80, 75, 4, 8]).buffer),
    },
  })),
}));

import {
  buildWorkflowsExportRows,
  buildWorkflowsXlsxBuffer,
  downloadWorkflowsExcel,
  IExportWorkflowsToExcelConfig,
  WORKFLOWS_XLSX_DEFAULT_FILENAME,
  WORKFLOWS_XLSX_MIME,
} from '../exportWorkflowsToExcel';
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

describe('exportWorkflowsToExcel', () => {
  describe('buildWorkflowsExportRows', () => {
    const baseConfig: IExportWorkflowsToExcelConfig = {
      workflows: [],
      users: [],
      groups: [],
      selectedFields: [],
      headerLabels: { ...systemHeaderLabels },
      multipleTasksLabel: 'Tasks',
      deletedGroupFallbackTemplate: 'Deleted Group (ID: {id})',
    };

    it('returns only header row when workflows array is empty', () => {
      const rows = buildWorkflowsExportRows({
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
      expect(rows).toHaveLength(1);
      expect(rows[0]).toEqual([
        'Workflow',
        'Template',
        'Starter',
        'Progress',
        'Step',
        'Performer',
      ]);
    });

    it('uses default system columns when selectedFields is empty and no optional fields', () => {
      const rows = buildWorkflowsExportRows({
        ...baseConfig,
        selectedFields: [],
        optionalFieldsFromWorkflow: [],
        headerLabels: systemHeaderLabels,
      });
      expect(rows[0]).toEqual([
        'Workflow',
        'Template',
        'Starter',
        'Progress',
        'Step',
        'Performer',
      ]);
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
      const rows = buildWorkflowsExportRows({
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
      expect(rows).toHaveLength(2);
      expect(rows[0]).toEqual([
        'Workflow',
        'Template',
        'Starter',
        'Progress',
        'Step',
        'Performer',
      ]);
      expect(rows[1]).toEqual([
        'My Process',
        'T1',
        'Alice Smith',
        '50%',
        'Task A',
        '',
      ]);
    });

    it('keeps raw cell values with comma and double quote without CSV escaping', () => {
      const workflows = [
        minimalWorkflow({ name: 'Name with "quotes" and, comma' }),
      ];
      const rows = buildWorkflowsExportRows({
        ...baseConfig,
        workflows,
        selectedFields: ['system-column-workflow'],
        headerLabels: { 'system-column-workflow': 'Name' },
      });
      expect(rows[1][0]).toBe('Name with "quotes" and, comma');
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
      const rows = buildWorkflowsExportRows({
        ...baseConfig,
        workflows,
        selectedFields: ['system-column-workflow', 'field-custom'],
        optionalFieldsFromWorkflow: optionalFields,
        headerLabels: {
          ...systemHeaderLabels,
          'field-custom': 'Custom',
        },
      });
      expect(rows[0]).toContain('Custom');
      expect(rows[1]).toContain('Custom value');
    });

    it('uses localized multipleTasksLabel for step when areMultipleTasks is true', () => {
      const workflows = [
        minimalWorkflow({ areMultipleTasks: true, oneActiveTaskName: null }),
      ];
      const rows = buildWorkflowsExportRows({
        ...baseConfig,
        workflows,
        selectedFields: ['system-column-step'],
        headerLabels: { 'system-column-step': 'Step' },
        multipleTasksLabel: 'Localized Multiple Tasks',
      });
      expect(rows[1][0]).toBe('Localized Multiple Tasks');
    });

    it('uses deletedGroupFallbackTemplate for performer when group is not in list', () => {
      const workflows = [
        minimalWorkflow({
          selectedUsers: [
            { type: ETemplateOwnerType.UserGroup, sourceId: 999 },
          ],
        }),
      ];
      const rows = buildWorkflowsExportRows({
        ...baseConfig,
        workflows,
        groups: [],
        selectedFields: ['system-column-performer'],
        headerLabels: { 'system-column-performer': 'Performer' },
        deletedGroupFallbackTemplate: 'Deleted Group (ID: {id})',
      });
      expect(rows[1][0]).toBe('Deleted Group (ID: 999)');
    });
  });

  describe('buildWorkflowsXlsxBuffer', () => {
    it('returns non-empty buffer for sample rows', async () => {
      const buffer = await buildWorkflowsXlsxBuffer([
        ['A', 'B'],
        ['1', '2'],
      ]);
      expect(buffer).toBeDefined();
      expect(buffer.byteLength).toBeGreaterThan(0);
    });
  });

  describe('downloadWorkflowsExcel', () => {
    it('creates xlsx blob and triggers download', () => {
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

      const sampleBuffer = new ArrayBuffer(8);
      downloadWorkflowsExcel(sampleBuffer, 'export.xlsx');

      expect(createObjectURL).toHaveBeenCalledTimes(1);
      const callArgs = (createObjectURL as jest.Mock).mock.calls[0];
      const blob = callArgs?.[0] as Blob | undefined;
      expect(blob).toBeDefined();
      expect(blob?.type).toBe(WORKFLOWS_XLSX_MIME);
      expect(blob?.size).toBeGreaterThan(0);
      expect(mockLink.setAttribute).toHaveBeenCalledWith('href', 'blob:mock-url');
      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'export.xlsx');
      expect(click).toHaveBeenCalled();
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');

      createElement.mockRestore();
      URL.createObjectURL = originalCreateObjectURL;
      URL.revokeObjectURL = originalRevokeObjectURL;
    });

    it('uses default WORKFLOWS_XLSX_DEFAULT_FILENAME when not provided', () => {
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

      downloadWorkflowsExcel(new ArrayBuffer(4));

      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', WORKFLOWS_XLSX_DEFAULT_FILENAME);

      URL.createObjectURL = originalCreateObjectURL;
      URL.revokeObjectURL = originalRevokeObjectURL;
    });
  });
});

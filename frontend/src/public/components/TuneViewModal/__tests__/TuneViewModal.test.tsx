import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { enMessages } from '../../../lang/locales/en_US';

import { TTransformedTask, TRuntimeMergedOutputPart, EExtraFieldType, IExtraField } from '../../../types/template';

const mockDispatch = jest.fn();

jest.mock('react-redux', () => ({
  useSelector: jest.fn((selector: (state: unknown) => unknown) => selector({})),
  useDispatch: () => mockDispatch,
}));

const mockIsOpen = jest.fn().mockReturnValue(true);
const mockTemplatesIdsFilter = jest.fn().mockReturnValue([100]);
const mockSavedFields = jest.fn().mockReturnValue([] as string[]);

jest.mock('../../../redux/selectors/workflows', () => ({
  getIsTuneViewModalOpen: () => mockIsOpen(),
  getWorkflowTemplatesIdsFilter: () => mockTemplatesIdsFilter(),
  getSavedFields: () => mockSavedFields(),
}));

const mockTemplateTasks = jest.fn().mockReturnValue([] as TTransformedTask[]);
const mockTemplateVariables = jest.fn().mockReturnValue([]);

jest.mock('../../../redux/selectors/templates', () => ({
  getTemplatesTasks: () => () => mockTemplateTasks(),
  getTemplatesVariables: () => () => mockTemplateVariables(),
}));

jest.mock('../../../hooks/useDelayUnmount', () => ({
  useDelayUnmount: () => true,
}));

jest.mock('../../../redux/workflows/slice', () => ({
  closeTuneViewModal: jest.fn(() => ({ type: 'closeTuneViewModal' })),
  setFilterSelectedFields: jest.fn((payload: string[]) => ({ type: 'setFilterSelectedFields', payload })),
  saveWorkflowsPreset: jest.fn((payload: Record<string, unknown>) => ({ type: 'saveWorkflowsPreset', payload })),
}));

jest.mock('../../UI', () => ({
  Button: ({ label, onClick }: { label: string; onClick: () => void }) =>
    React.createElement('button', { onClick, 'data-testid': `btn-${label}` }, label),
  Checkbox: ({ title, checked, onChange, checkboxId }: {
    title: string; checked: boolean; onChange: () => void; checkboxId: string;
    titlePosition?: string; labelClassName?: string; disabled?: boolean;
  }) =>
    React.createElement('input', {
      type: 'checkbox',
      checked,
      onChange,
      'data-testid': `cb-${checkboxId}`,
      'aria-label': title,
    }),
  SideModal: Object.assign(
    ({ children }: { children: React.ReactNode }) =>
      React.createElement('div', { 'data-testid': 'side-modal' }, children),
    {
      Header: ({ children }: { children: React.ReactNode }) =>
        React.createElement('div', { 'data-testid': 'side-modal-header' }, children),
      Body: ({ children }: { children: React.ReactNode }) =>
        React.createElement('div', { 'data-testid': 'side-modal-body' }, children),
      Footer: ({ children }: { children: React.ReactNode }) =>
        React.createElement('div', { 'data-testid': 'side-modal-footer' }, children),
    },
  ),
  Tooltip: ({ children }: { children: React.ReactNode }) =>
    React.createElement('span', null, children),
}));

jest.mock('../../icons', () => ({
  ShortArrowIcon: () => null,
}));

jest.mock('../../StepName', () => ({
  StepName: () => null,
}));

jest.mock('../../TemplateEdit/TooltipRichContent', () => ({
  TooltipRichContent: () => null,
}));

import { TuneViewModal } from '../TuneViewModal';

const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName: 'field-1',
  name: 'Field 1',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

const makeFieldsetOutput = (
  apiName: string,
  name: string,
  fields: IExtraField[],
): TRuntimeMergedOutputPart => ({
  kind: 'fieldset' as const,
  data: { apiName, name, description: '', fields, order: 0 },
});

const makeFieldOutput = (field: IExtraField): TRuntimeMergedOutputPart => ({
  kind: 'field' as const,
  field,
});

const makeTask = (apiName: string, name: string, mergedOutputs: TRuntimeMergedOutputPart[]): TTransformedTask => ({
  apiName,
  name,
  mergedOutputs,
});

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    React.createElement(IntlProvider, { locale: 'en', messages: enMessages }, ui),
  );

describe('TuneViewModal', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsOpen.mockReturnValue(true);
    mockTemplatesIdsFilter.mockReturnValue([100]);
    mockSavedFields.mockReturnValue([]);
    mockTemplateTasks.mockReturnValue([]);
    mockTemplateVariables.mockReturnValue([]);
  });

  describe('Fieldsets', () => {
    it('renders fieldset group with title and field checkboxes', () => {
      const fsField1 = makeField({ apiName: 'fs-f1', name: 'FS Field 1' });
      const fsField2 = makeField({ apiName: 'fs-f2', name: 'FS Field 2' });
      const regularField = makeField({ apiName: 'reg-1', name: 'Regular' });

      const task = makeTask('task-1', 'Task 1', [
        makeFieldOutput(regularField),
        makeFieldsetOutput('fs-1', 'My Fieldset', [fsField1, fsField2]),
      ]);

      mockTemplateTasks.mockReturnValue([task]);
      mockSavedFields.mockReturnValue(['reg-1']);

      renderWithIntl(React.createElement(TuneViewModal));

      expect(screen.getByText('My Fieldset')).toBeInTheDocument();
      expect(screen.getByTestId('cb-fs-f1')).toBeInTheDocument();
      expect(screen.getByTestId('cb-fs-f2')).toBeInTheDocument();
      expect(screen.getByTestId('cb-reg-1')).toBeInTheDocument();
    });

    it('toggles fieldset field checked state', () => {
      const fsField = makeField({ apiName: 'fs-toggle', name: 'Toggle Me' });
      const task = makeTask('task-1', 'Task 1', [
        makeFieldsetOutput('fs-1', 'FS', [fsField]),
      ]);

      mockTemplateTasks.mockReturnValue([task]);
      mockSavedFields.mockReturnValue(['fs-toggle']);

      renderWithIntl(React.createElement(TuneViewModal));

      const checkbox = screen.getByTestId('cb-fs-toggle') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);

      userEvent.click(checkbox);

      expect(screen.getByTestId('cb-fs-toggle')).toBeInTheDocument();
    });

    it('auto-expands task when a fieldset field is in savedFields', () => {
      const fsField = makeField({ apiName: 'fs-saved', name: 'Saved FS Field' });
      const task = makeTask('task-auto', 'Auto Task', [
        makeFieldsetOutput('fs-auto', 'Auto FS', [fsField]),
      ]);

      mockTemplateTasks.mockReturnValue([task]);
      mockSavedFields.mockReturnValue(['fs-saved']);

      renderWithIntl(React.createElement(TuneViewModal));

      expect(screen.getByText('Auto FS')).toBeInTheDocument();
      expect(screen.getByTestId('cb-fs-saved')).toBeInTheDocument();
    });

    it('Apply changes includes fieldset fields in orderedFields with sequential order', () => {
      const { saveWorkflowsPreset } = require('../../../redux/workflows/slice');

      const regularField = makeField({ apiName: 'reg-1', name: 'Reg' });
      const fsField1 = makeField({ apiName: 'fs-f1', name: 'FS F1' });
      const fsField2 = makeField({ apiName: 'fs-f2', name: 'FS F2' });

      const task = makeTask('task-1', 'Task 1', [
        makeFieldOutput(regularField),
        makeFieldsetOutput('fs-1', 'FS', [fsField1, fsField2]),
      ]);

      mockTemplateTasks.mockReturnValue([task]);
      mockSavedFields.mockReturnValue(['reg-1', 'fs-f1', 'fs-f2']);

      renderWithIntl(React.createElement(TuneViewModal));

      const applyBtn = screen.getAllByRole('button').find(
        (btn) => btn.textContent?.toLowerCase().includes('apply'),
      );
      if (!applyBtn) throw new Error('Apply button not found');
      userEvent.click(applyBtn);

      expect(saveWorkflowsPreset).toHaveBeenCalledTimes(1);
      expect(saveWorkflowsPreset).toHaveBeenCalledWith(
        expect.objectContaining({
          templateId: 100,
          type: 'personal',
          orderedFields: expect.arrayContaining([
            expect.objectContaining({ apiName: 'reg-1', order: 1 }),
            expect.objectContaining({ apiName: 'fs-f1', order: 2 }),
            expect.objectContaining({ apiName: 'fs-f2', order: 3 }),
          ]),
        }),
      );
    });
  });
});

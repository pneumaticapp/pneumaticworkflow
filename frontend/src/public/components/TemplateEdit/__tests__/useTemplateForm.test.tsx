/// <reference types="jest" />
import * as React from 'react';
import { act, render } from '@testing-library/react';

import {
  ITemplate,
  ITemplateTask,
  ETaskPerformerType,
} from '../../../types/template';
import { EConditionAction, EConditionOperators, EConditionLogicOperations, TConditionRule } from '../TaskForm/Conditions/types';
import { TemplateForm, useTemplateField, useTemplateForm, useTemplatePersist, useTemplateSaveRetry } from '../useTemplateForm';
import { TEMPLATE_FORM_PERSIST_DEBOUNCE_MS } from '../useTemplateForm/TemplateFormPersistProvider';
import { getTemplateVariablesFingerprint } from '../useTemplateForm/templateFormUtils';
import { patchTemplate, saveTemplate, setTemplateStatus } from '../../../redux/actions';
import { ETemplateStatus } from '../../../types/redux';
import {
  abandonAutosavePersistRequests,
  allocateAutosavePersistRequest,
  createAutosavePersistScope,
  isAutosavePersistRequestCurrent,
} from '../../../redux/template/persistRequest';

const mockDispatch = jest.fn();

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(() => mockDispatch),
  connect: () => (component: unknown) => component,
}));

jest.mock('../../../redux/actions', () => ({
  ...jest.requireActual('../../../redux/actions'),
  patchTemplate: jest.fn((payload: unknown) => ({ type: 'PATCH_TEMPLATE', payload })),
  saveTemplate: jest.fn((payload?: unknown) => ({ type: 'SAVE_TEMPLATE', payload })),
}));

beforeAll(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.clearAllTimers();
});

afterAll(() => {
  jest.useRealTimers();
});

const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask =>
  ({
    apiName: 'task-1',
    number: 1,
    name: 'Test Task',
    description: '',
    delay: null,
    rawDueDate: null as any,
    requireCompletionByAll: false,
    skipForStarter: false,
    rawPerformers: [],
    fields: [],
    uuid: 'uuid-1',
    conditions: [],
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  }) as ITemplateTask;

const makeTemplate = (overrides: Partial<ITemplate> = {}): ITemplate =>
  ({
    id: 1,
    name: 'Template',
    description: '',
    isActive: true,
    finalizable: false,
    completionNotification: false,
    reminderNotification: false,
    dateUpdated: null,
    updatedBy: null,
    owners: [],
    kickoff: { description: '', fields: [] } as any,
    tasks: [makeTask()],
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 1,
    performersCount: 0,
    ...overrides,
  }) as ITemplate;

describe('autosave persist request scope', () => {
  it('does not invalidate another editor session', () => {
    const firstScope = createAutosavePersistScope();
    const secondScope = createAutosavePersistScope();
    const firstRequest = allocateAutosavePersistRequest(firstScope);

    allocateAutosavePersistRequest(secondScope);
    abandonAutosavePersistRequests(secondScope);

    expect(isAutosavePersistRequestCurrent(firstRequest)).toBe(true);
  });
});

describe('getTemplateVariablesFingerprint', () => {
  it('changes when variable metadata changes without changing the field count', () => {
    const field = {
      apiName: 'field-1',
      name: 'Original',
      type: 'string',
      selections: [],
      dataset: null,
    } as any;
    const template = makeTemplate({
      kickoff: { description: '', fields: [field] } as any,
    });

    expect(getTemplateVariablesFingerprint(template)).not.toBe(
      getTemplateVariablesFingerprint({
        ...template,
        kickoff: {
          ...template.kickoff,
          fields: [{ ...field, name: 'Renamed' }],
        },
      }),
    );
  });
});

interface ISpyHandle {
  values: ITemplate;
  setFieldValue: (field: string, value: unknown, shouldValidate?: boolean) => void;
  consumePendingChanges: (explicitFields?: Partial<ITemplate>) => Partial<ITemplate>;
  confirmConsumedChanges: () => void;
  revertConsumedChanges: () => void;
  abandonPendingChanges: () => void;
}

// Drain the persist provider's debounced flush plus the follow-up tick it
// schedules when it mirrors the saga's `isActive` deactivation, so no React
// state update leaks outside `act`. By default, simulates a successful autosave
// so the persist baseline advances before the next edit.
const flushPersist = (options?: { confirmSuccess?: boolean }) =>
  act(async () => {
    jest.advanceTimersByTime(TEMPLATE_FORM_PERSIST_DEBOUNCE_MS);
    await Promise.resolve();

    if (options?.confirmSuccess === false) {
      return;
    }

    const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
    const lastCall = calls[calls.length - 1];

    if (lastCall?.[0]?.onSuccess) {
      lastCall[0].onSuccess();
    }
  });

function TemplateFormHarness({
  initialTemplate,
  spy,
}: {
  initialTemplate: ITemplate;
  spy: (handle: ISpyHandle) => void;
}) {
  const { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef } = useTemplateForm(initialTemplate);

  const Spy: React.FC = () => {
    const { values, setFieldValue: contextSetFieldValue } = useTemplateField();
    const { consumePendingChanges, confirmConsumedChanges, revertConsumedChanges, abandonPendingChanges } = useTemplatePersist();
    spy({ values, setFieldValue: contextSetFieldValue, consumePendingChanges, confirmConsumedChanges, revertConsumedChanges, abandonPendingChanges });
    return null;
  };

  return (
    <TemplateForm
      formik={formik}
      setFieldValue={setFieldValue}
      setValues={setValues}
      dirtyRef={dirtyRef}
      pendingUserEditsRef={pendingUserEditsRef}
      persistBaselineSyncRef={persistBaselineSyncRef}
    >
      <Spy />
    </TemplateForm>
  );
}

function StatefulTemplateFormHarness({
  initialTemplate,
  spy,
}: {
  initialTemplate: ITemplate;
  spy: (handle: ISpyHandle) => void;
}) {
  return <TemplateFormHarness initialTemplate={initialTemplate} spy={spy} />;
}

describe('TemplateFormPersistProvider deactivation', () => {
  beforeEach(() => {
    (patchTemplate as unknown as jest.Mock).mockClear();
  });

  it('flips isActive to false in Formik immediately when a non-activation field changes', async () => {
    const template = makeTemplate({ isActive: true, description: 'old' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'new description', false);
    });

    expect(handle!.values.isActive).toBe(false);

    await flushPersist();
    expect(patchTemplate).toHaveBeenCalledTimes(1);
  });

  it('does not deactivate when only an activation-related field changes', async () => {
    const template = makeTemplate({ isActive: true, isPublic: false });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('isPublic', true, false);
    });

    await flushPersist();

    expect(handle!.values.isActive).toBe(true);
    expect(patchTemplate).toHaveBeenCalledTimes(1);
  });

  it('marks template as Saving before the deferred autosave flush', () => {
    const template = makeTemplate({ isActive: true, isPublic: false });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    mockDispatch.mockClear();
    (patchTemplate as unknown as jest.Mock).mockClear();

    act(() => {
      handle!.setFieldValue('isPublic', true, false);
    });

    expect(handle!.values.isActive).toBe(true);
    expect(mockDispatch).toHaveBeenCalledWith(setTemplateStatus(ETemplateStatus.Saving));
    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('does not deactivate when only kickoff.description changes (matches saga special case)', async () => {
    const template = makeTemplate({
      isActive: true,
      kickoff: { description: 'old kickoff', fields: [] } as any,
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('kickoff', { description: 'new kickoff', fields: [] }, false);
    });

    await flushPersist();

    expect(handle!.values.isActive).toBe(true);
  });

  it('deactivates when kickoff changes but description stays the same', async () => {
    const template = makeTemplate({
      isActive: true,
      kickoff: { description: 'same', fields: [] } as any,
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('kickoff', { description: 'same', fields: [{ apiName: 'f-1' }] }, false);
    });

    await flushPersist();

    expect(handle!.values.isActive).toBe(false);
  });

  it('deactivates when kickoff fields change even if description also changes', async () => {
    const template = makeTemplate({
      isActive: true,
      kickoff: { description: 'old kickoff', fields: [{ apiName: 'f-1' }] } as any,
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('kickoff', { description: 'new kickoff', fields: [] }, false);
    });

    await flushPersist();

    expect(handle!.values.isActive).toBe(false);
  });

  it('lets submit consume pending edits before the autosave dispatches', async () => {
    const template = makeTemplate({ isActive: true, owners: [] });
    let handle: ISpyHandle | null = null;
    const owners = [{ id: 1, role: 'owner' }] as any;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('owners', owners, false);
    });

    let pendingChanges: Partial<ITemplate> = {};
    act(() => {
      pendingChanges = handle!.consumePendingChanges();
    });
    await flushPersist();

    expect(pendingChanges).toEqual({ owners, isActive: false });
    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('restores the persist baseline and re-queues autosave when an explicit submit fails after consume', async () => {
    const template = makeTemplate({ isActive: true, owners: [] });
    let handle: ISpyHandle | null = null;
    const owners = [{ id: 1, role: 'owner' }] as any;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('owners', owners, false);
    });

    act(() => {
      handle!.consumePendingChanges();
      handle!.revertConsumedChanges();
    });
    await flushPersist();

    expect(handle!.values.owners).toEqual(owners);
    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      owners,
      isActive: false,
    });
  });

  it('keeps consumed edits visible in Formik after a failed explicit submit', async () => {
    const template = makeTemplate({ isActive: true, name: 'Original', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('name', 'Unsaved edit', false);
      handle!.consumePendingChanges();
      handle!.revertConsumedChanges();
    });

    expect(handle!.values.name).toBe('Unsaved edit');
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      name: 'Unsaved edit',
      isActive: false,
    });
  });

  it('reverts explicit activation fields in Formik after a failed submit', async () => {
    const template = makeTemplate({ isActive: false, name: 'Original', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('name', 'Unsaved edit', false);
      handle!.setFieldValue('isActive', true, false);
    });

    act(() => {
      handle!.consumePendingChanges({ isActive: true });
      handle!.revertConsumedChanges();
    });

    expect(handle!.values.name).toBe('Unsaved edit');
    expect(handle!.values.isActive).toBe(false);
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      name: 'Unsaved edit',
    });
  });

  it('re-queues autosave on failed activation when isActive was not flipped in Formik', () => {
    const template = makeTemplate({ isActive: false, name: 'Original', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('name', 'Unsaved edit', false);
    });

    act(() => {
      handle!.consumePendingChanges({ isActive: true });
    });

    const callsBeforeRevert = (patchTemplate as unknown as jest.Mock).mock.calls.length;

    act(() => {
      handle!.revertConsumedChanges();
    });

    const callsAfterRevert = (patchTemplate as unknown as jest.Mock).mock.calls.slice(callsBeforeRevert);

    expect(handle!.values.name).toBe('Unsaved edit');
    expect(handle!.values.isActive).toBe(false);
    expect(callsAfterRevert).toHaveLength(1);
    expect(callsAfterRevert[0][0].changedFields).toEqual({
      name: 'Unsaved edit',
    });
  });

  it('re-queues autosave after a failed explicit submit when Redux reinitializes during the in-flight patch', async () => {
    const template = makeTemplate({ isActive: true, owners: [] });
    let handle: ISpyHandle | null = null;
    const owners = [{ id: 1, role: 'owner' }] as any;

    const { rerender } = render(
      <StatefulTemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />,
    );

    act(() => {
      handle!.setFieldValue('owners', owners, false);
    });

    act(() => {
      handle!.consumePendingChanges();
    });

    act(() => {
      rerender(
        <StatefulTemplateFormHarness
          initialTemplate={{
            ...template,
            owners,
            isActive: false,
          }}
          spy={(h) => { handle = h; }}
        />,
      );
    });

    expect(handle!.values.owners).toEqual(owners);

    act(() => {
      handle!.revertConsumedChanges();
    });
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      owners,
      isActive: false,
    });
  });

  it('does not restore the persist baseline after an explicit submit succeeds', async () => {
    const template = makeTemplate({ isActive: true, owners: [] });
    let handle: ISpyHandle | null = null;
    const owners = [{ id: 1, role: 'owner' }] as any;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('owners', owners, false);
    });

    act(() => {
      handle!.consumePendingChanges();
      handle!.confirmConsumedChanges();
    });
    await flushPersist();

    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('preserves edits made after consume when an explicit submit succeeds', () => {
    const template = makeTemplate({ isActive: true, name: 'Original', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />,
    );

    act(() => {
      handle!.setFieldValue('name', 'Submit edit', false);
      handle!.consumePendingChanges();
      handle!.setFieldValue('name', 'Post-submit edit', false);
      handle!.confirmConsumedChanges();
    });

    rerender(
      <StatefulTemplateFormHarness
        initialTemplate={{
          ...template,
          name: 'Submit edit',
          isActive: false,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        spy={(h) => { handle = h; }}
      />,
    );

    expect(handle!.values.name).toBe('Post-submit edit');
  });

  it('persists the latest value when two edits land before the deferred flush runs', async () => {
    const template = makeTemplate({ isActive: true, description: 'old' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'first edit', false);
      handle!.setFieldValue('description', 'second edit', false);
    });
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      description: 'second edit',
      isActive: false,
    });
  });

  it('persists the latest value when two separate edits each render before the deferred flush runs', async () => {
    const template = makeTemplate({ isActive: false, description: 'old' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    // Two separate user events (separate acts) — each produces its own render
    // and resets the debounced flush timer. After the debounce window, only the
    // latest value should be persisted.
    act(() => {
      handle!.setFieldValue('description', 'first edit', false);
    });
    act(() => {
      handle!.setFieldValue('description', 'second edit', false);
    });
    await flushPersist();

    const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
    const descriptionPatches = calls
      .map((c: any[]) => c[0]?.changedFields?.description)
      .filter((v: unknown) => v !== undefined);

    expect(descriptionPatches).toEqual(['second edit']);
    expect(patchTemplate).toHaveBeenCalledTimes(1);
  });

  it('flushes edits made during an in-flight autosave after the first patch succeeds', async () => {
    const template = makeTemplate({ isActive: true, description: 'old', name: 'Original' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'first edit', false);
    });

    await flushPersist({ confirmSuccess: false });

    act(() => {
      const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
      calls[calls.length - 1][0].onSuccess();
    });

    act(() => {
      handle!.setFieldValue('name', 'second edit', false);
    });

    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(2);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[1][0].changedFields).toEqual({
      name: 'second edit',
    });
  });

  it('ignores stale autosave callbacks superseded by a newer patchTemplate dispatch', async () => {
    const template = makeTemplate({ isActive: true, description: 'old', name: 'Original' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'first edit', false);
    });
    await flushPersist({ confirmSuccess: false });

    const firstOnSuccess = (patchTemplate as unknown as jest.Mock).mock.calls[0][0].onSuccess;

    act(() => {
      handle!.setFieldValue('name', 'second edit', false);
    });
    await flushPersist({ confirmSuccess: false });

    expect(patchTemplate).toHaveBeenCalledTimes(2);

    act(() => {
      firstOnSuccess();
    });

    expect(handle!.values.name).toBe('second edit');

    act(() => {
      const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
      calls[calls.length - 1][0].onSuccess();
    });

    act(() => {
      handle!.setFieldValue('description', 'third edit', false);
    });
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(3);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[2][0].changedFields).toEqual({
      description: 'third edit',
    });
  });

  it('does not dispatch patchTemplate on unmount after abandoning pending edits', async () => {
    const template = makeTemplate({ isActive: true, description: 'old' });
    let handle: ISpyHandle | null = null;

    const { unmount } = render(
      <TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />,
    );

    act(() => {
      handle!.setFieldValue('description', 'discarded edit', false);
      handle!.abandonPendingChanges();
    });

    act(() => {
      unmount();
    });

    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({});
  });

  it('ignores in-flight autosave callbacks after abandoning pending edits', async () => {
    const template = makeTemplate({ isActive: true, description: 'old', name: 'Original' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'discarded edit', false);
    });
    await flushPersist({ confirmSuccess: false });

    const abandonedOnSuccess = (patchTemplate as unknown as jest.Mock).mock.calls[0][0].onSuccess;

    act(() => {
      handle!.abandonPendingChanges();
    });

    expect(patchTemplate).toHaveBeenCalledTimes(2);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[1][0].changedFields).toEqual({});

    act(() => {
      handle!.setFieldValue('name', 'kept edit', false);
    });
    await flushPersist({ confirmSuccess: false });

    act(() => {
      abandonedOnSuccess();
    });

    expect(handle!.values.name).toBe('kept edit');

    act(() => {
      const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
      calls[calls.length - 1][0].onSuccess();
    });

    act(() => {
      handle!.setFieldValue('description', 'next edit', false);
    });
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(4);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[3][0].changedFields).toEqual({
      description: 'next edit',
    });
  });

  it('dispatches patchTemplate on unmount when pending edits were not flushed', async () => {
    const template = makeTemplate({ isActive: true, description: 'old' });
    let handle: ISpyHandle | null = null;

    const { unmount } = render(
      <TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />,
    );

    act(() => {
      handle!.setFieldValue('description', 'unsaved edit', false);
    });

    act(() => {
      unmount();
    });

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      description: 'unsaved edit',
      isActive: false,
    });
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].templateSnapshot).toEqual({
      ...template,
      description: 'unsaved edit',
      isActive: false,
    });
  });

  it('still persists a second edit when the first triggers an isActive deactivation', async () => {
    const template = makeTemplate({ isActive: true, description: 'old' });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'first edit', false);
    });
    act(() => {
      handle!.setFieldValue('description', 'second edit', false);
    });
    await flushPersist();

    const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
    const descriptionPatches = calls
      .map((c: any[]) => c[0]?.changedFields?.description)
      .filter((v: unknown) => v !== undefined);

    expect(descriptionPatches).toEqual(['second edit']);
    expect(handle!.values.isActive).toBe(false);
  });
});

describe('useTemplateForm reinitialize', () => {
  function HookHarness({
    currentTemplate,
    templateIdentityKey,
    onReady,
  }: {
    currentTemplate: ITemplate;
    templateIdentityKey?: string | number;
    onReady(result: ReturnType<typeof useTemplateForm>): void;
  }) {
    const result = useTemplateForm(currentTemplate, templateIdentityKey);
    onReady(result);
    return null;
  }

  it('drops pending edits from a previous template when the template identity changes', () => {
    const templateA = makeTemplate({ id: 1, name: 'Template A', dateUpdated: null });
    const templateB = makeTemplate({ id: 2, name: 'Template B', dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={templateA}
        templateIdentityKey={1}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('name', 'Edited on A', false);
    });

    rerender(
      <HookHarness
        currentTemplate={templateB}
        templateIdentityKey={2}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.name).toBe('Template B');
    expect(hookResult!.pendingUserEditsRef.current).toEqual({});
    expect(hookResult!.dirtyRef.current).toBe(false);
  });

  it('preserves pending edits when a new template receives its first id after create autosave', () => {
    const newTemplate = makeTemplate({ id: undefined, name: 'New', dateUpdated: null });
    const savedTemplate = { ...newTemplate, id: 42 };
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={newTemplate}
        templateIdentityKey="create:/templates/create/"
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('name', 'Edited during create save', false);
    });

    rerender(
      <HookHarness
        currentTemplate={savedTemplate}
        templateIdentityKey={42}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.name).toBe('Edited during create save');
    expect(hookResult!.pendingUserEditsRef.current.name).toBe('Edited during create save');
    expect(hookResult!.dirtyRef.current).toBe(true);
  });

  it('drops pending edits when switching between create flows', () => {
    const newTemplate = makeTemplate({ id: undefined, name: 'Draft', dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={newTemplate}
        templateIdentityKey="create:/templates/create/"
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('name', 'Manual draft', false);
    });

    rerender(
      <HookHarness
        currentTemplate={{ ...newTemplate, name: 'AI Template' }}
        templateIdentityKey="create:/templates/create-with-ai/"
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.name).toBe('AI Template');
    expect(hookResult!.pendingUserEditsRef.current).toEqual({});
    expect(hookResult!.dirtyRef.current).toBe(false);
  });

  it('merges pending user edits into resolved Formik initialValues', () => {
    const template = makeTemplate({ name: 'Original', dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('name', 'unsaved edit', false);
    });

    rerender(
      <HookHarness
        currentTemplate={{
          ...template,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.name).toBe('unsaved edit');
    expect(hookResult!.formik.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
  });

  it('merges nested task field edits instead of storing dotted Formik paths as top-level keys', () => {
    const task = makeTask({ name: 'Original Task' });
    const template = makeTemplate({ tasks: [task], dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('tasks.0.name', 'Edited Task', false);
    });

    expect(hookResult!.pendingUserEditsRef.current).toEqual({
      isActive: false,
      tasks: [expect.objectContaining({ name: 'Edited Task' })],
    });
    expect(Object.prototype.hasOwnProperty.call(hookResult!.pendingUserEditsRef.current, 'tasks.0.name')).toBe(false);

    rerender(
      <HookHarness
        currentTemplate={{
          ...template,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.tasks[0].name).toBe('Edited Task');
    expect(hookResult!.formik.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
    expect(Object.prototype.hasOwnProperty.call(hookResult!.formik.values, 'tasks.0.name')).toBe(false);
  });

  it('merges whole-task updates via tasks[index] paths into pending edits', () => {
    const task = makeTask({ name: 'Original Task', skipForStarter: false });
    const template = makeTemplate({ tasks: [task], dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('tasks.0', { ...task, skipForStarter: true }, false);
    });

    expect(hookResult!.pendingUserEditsRef.current).toEqual({
      isActive: false,
      tasks: [expect.objectContaining({ skipForStarter: true })],
    });
    expect(Object.prototype.hasOwnProperty.call(hookResult!.pendingUserEditsRef.current, 'tasks.0')).toBe(false);
  });

  it('preserves incoming-only tasks when Redux reinitializes during pending task edits', () => {
    const task1 = makeTask({ apiName: 'task-1', uuid: 'uuid-1', number: 1, name: 'Original' });
    const task2 = makeTask({ apiName: 'task-2', uuid: 'uuid-2', number: 2, name: 'Server Added' });
    const template = makeTemplate({ tasks: [task1], dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('tasks.0.name', 'Edited Task', false);
    });

    rerender(
      <HookHarness
        currentTemplate={{
          ...template,
          tasks: [task1, task2],
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.tasks).toHaveLength(2);
    expect(hookResult!.formik.values.tasks[0].name).toBe('Edited Task');
    expect(hookResult!.formik.values.tasks[1].name).toBe('Server Added');
    expect(hookResult!.formik.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
  });

  it('interleaves server-added tasks by number when Redux reinitializes during pending task edits', () => {
    const task1 = makeTask({ apiName: 'task-1', uuid: 'uuid-1', number: 1, name: 'Task 1' });
    const task3 = makeTask({ apiName: 'task-3', uuid: 'uuid-3', number: 3, name: 'Task 3' });
    const task2 = makeTask({ apiName: 'task-2', uuid: 'uuid-2', number: 2, name: 'Server Inserted' });
    const template = makeTemplate({ tasks: [task1, task3], dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('tasks.0.name', 'Edited Task 1', false);
      hookResult!.setFieldValue('tasks.1.name', 'Edited Task 3', false);
    });

    rerender(
      <HookHarness
        currentTemplate={{
          ...template,
          tasks: [task1, task2, task3],
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.tasks).toHaveLength(3);
    expect(hookResult!.formik.values.tasks.map((task) => task.name)).toEqual([
      'Edited Task 1',
      'Server Inserted',
      'Edited Task 3',
    ]);
    expect(hookResult!.formik.values.tasks.map((task) => task.number)).toEqual([1, 2, 3]);
  });

  it('does not restore locally deleted tasks when Redux reinitializes before the deletion is saved', () => {
    const task1 = makeTask({ apiName: 'task-1', uuid: 'uuid-1', number: 1, name: 'Task 1' });
    const task2 = makeTask({ apiName: 'task-2', uuid: 'uuid-2', number: 2, name: 'Task 2' });
    const template = makeTemplate({ tasks: [task1, task2], dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('tasks', [task1], false);
    });

    expect(hookResult!.formik.values.tasks).toHaveLength(1);
    expect(hookResult!.formik.values.tasks[0].uuid).toBe('uuid-1');

    rerender(
      <HookHarness
        currentTemplate={{
          ...template,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.tasks).toHaveLength(1);
    expect(hookResult!.formik.values.tasks[0].uuid).toBe('uuid-1');
    expect(hookResult!.formik.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
  });

  it('preserves locally added tasks when Redux reinitializes before the addition is saved', () => {
    const task1 = makeTask({ apiName: 'task-1', uuid: 'uuid-1', number: 1, name: 'Task 1' });
    const localTask = makeTask({ apiName: 'task-local', uuid: 'uuid-local', number: 2, name: 'Local Task' });
    const template = makeTemplate({ tasks: [task1], dateUpdated: null });
    let hookResult: ReturnType<typeof useTemplateForm> | null = null;

    const { rerender } = render(
      <HookHarness
        currentTemplate={template}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    act(() => {
      hookResult!.setFieldValue('tasks', [task1, localTask], false);
    });

    rerender(
      <HookHarness
        currentTemplate={{
          ...template,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        onReady={(result) => { hookResult = result; }}
      />,
    );

    expect(hookResult!.formik.values.tasks).toHaveLength(2);
    expect(hookResult!.formik.values.tasks.map((task) => task.uuid)).toEqual(['uuid-1', 'uuid-local']);
    expect(hookResult!.formik.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
  });
});

describe('TemplateFormPersistProvider reinitialize', () => {
  beforeEach(() => {
    (patchTemplate as unknown as jest.Mock).mockClear();
  });

  it('preserves Formik-only edits when Redux reinitializes during an in-flight save', async () => {
    const template = makeTemplate({ isActive: true, name: 'Original', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness
        initialTemplate={template}
        spy={(h) => { handle = h; }}
      />,
    );

    act(() => {
      handle!.setFieldValue('description', 'saved edit', false);
    });
    await flushPersist();

    rerender(
      <StatefulTemplateFormHarness
        initialTemplate={{
          ...template,
          description: 'saved edit',
          isActive: false,
        }}
        spy={(h) => { handle = h; }}
      />,
    );
    await flushPersist();

    (patchTemplate as unknown as jest.Mock).mockClear();

    act(() => {
      handle!.setFieldValue('name', 'unsaved edit', false);
      rerender(
        <StatefulTemplateFormHarness
          initialTemplate={{
            ...template,
            description: 'saved edit',
            isActive: false,
            dateUpdated: '2026-07-01T00:00:00Z',
          }}
          spy={(h) => { handle = h; }}
        />,
      );
    });

    await flushPersist();

    expect(handle!.values.name).toBe('unsaved edit');
    expect(handle!.values.description).toBe('saved edit');
    expect(handle!.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      name: 'unsaved edit',
    });
  });

  it('does not treat a Redux reinitialize as a user edit when Formik has no pending changes', async () => {
    const template = makeTemplate({ isActive: true, description: 'old', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness
        initialTemplate={template}
        spy={(h) => { handle = h; }}
      />,
    );

    act(() => {
      handle!.setFieldValue('description', 'new', false);
    });
    await flushPersist();

    (patchTemplate as unknown as jest.Mock).mockClear();

    rerender(
      <StatefulTemplateFormHarness
        initialTemplate={{
          ...template,
          description: 'new',
          isActive: false,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        spy={(h) => { handle = h; }}
      />,
    );

    await flushPersist();

    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('does not re-dispatch externally reinitialized fields when a different edit is pending', async () => {
    const template = makeTemplate({
      isActive: true,
      name: 'Original',
      dateUpdated: null,
      owners: [],
    });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness
        initialTemplate={template}
        spy={(h) => { handle = h; }}
      />,
    );

    act(() => {
      handle!.setFieldValue('name', 'unsaved edit', false);
    });

    (patchTemplate as unknown as jest.Mock).mockClear();

    act(() => {
      rerender(
        <StatefulTemplateFormHarness
          initialTemplate={{
            ...template,
            dateUpdated: '2026-07-01T00:00:00Z',
            owners: [{ id: 1, role: 'owner' }] as any,
          }}
          spy={(h) => { handle = h; }}
        />,
      );
    });

    await flushPersist();

    expect(handle!.values.name).toBe('unsaved edit');
    expect(handle!.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
    expect(handle!.values.owners).toEqual([{ id: 1, role: 'owner' }]);
    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      name: 'unsaved edit',
      isActive: false,
    });
  });

  it('does not re-dispatch normalized nested values after autosave succeeds', async () => {
    const task = makeTask({ name: 'Original Task' });
    const template = makeTemplate({ isActive: true, tasks: [task], dateUpdated: null });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />,
    );

    act(() => {
      handle!.setFieldValue('tasks.0.name', 'Edited Task', false);
    });
    await flushPersist({ confirmSuccess: false });

    rerender(
      <StatefulTemplateFormHarness
        initialTemplate={{
          ...template,
          isActive: false,
          tasks: [{ ...task, name: 'Edited Task', ancestors: [] }],
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        spy={(h) => { handle = h; }}
      />,
    );

    act(() => {
      (patchTemplate as unknown as jest.Mock).mock.calls[0][0].onSuccess();
      jest.advanceTimersByTime(TEMPLATE_FORM_PERSIST_DEBOUNCE_MS);
    });

    expect(patchTemplate).toHaveBeenCalledTimes(1);
  });

  it('does not re-dispatch server-stamped fields on the next edit after autosave succeeds', async () => {
    const template = makeTemplate({ isActive: true, description: 'old', dateUpdated: null });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness
        initialTemplate={template}
        spy={(h) => { handle = h; }}
      />,
    );

    act(() => {
      handle!.setFieldValue('description', 'saved edit', false);
    });
    await flushPersist();

    rerender(
      <StatefulTemplateFormHarness
        initialTemplate={{
          ...template,
          description: 'saved edit',
          isActive: false,
          dateUpdated: '2026-07-01T00:00:00Z',
        }}
        spy={(h) => { handle = h; }}
      />,
    );
    await flushPersist();

    (patchTemplate as unknown as jest.Mock).mockClear();

    act(() => {
      handle!.setFieldValue('name', 'next edit', false);
    });
    await flushPersist();

    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      name: 'next edit',
    });
  });

  it('preserves nested task edits and sends valid changedFields after Redux reinitializes', async () => {
    const task = makeTask({ name: 'Original Task' });
    const template = makeTemplate({ isActive: true, tasks: [task], dateUpdated: null });
    let handle: ISpyHandle | null = null;

    const { rerender } = render(
      <StatefulTemplateFormHarness
        initialTemplate={template}
        spy={(h) => { handle = h; }}
      />,
    );

    act(() => {
      handle!.setFieldValue('tasks.0.name', 'Edited Task', false);
      rerender(
        <StatefulTemplateFormHarness
          initialTemplate={{
            ...template,
            dateUpdated: '2026-07-01T00:00:00Z',
          }}
          spy={(h) => { handle = h; }}
        />,
      );
    });

    await flushPersist();

    expect(handle!.values.tasks[0].name).toBe('Edited Task');
    expect(handle!.values.dateUpdated).toBe('2026-07-01T00:00:00Z');
    expect(Object.prototype.hasOwnProperty.call(handle!.values, 'tasks.0.name')).toBe(false);
    expect(patchTemplate).toHaveBeenCalledTimes(1);
    expect((patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields).toEqual({
      isActive: false,
      tasks: [expect.objectContaining({ name: 'Edited Task' })],
    });
    expect(Object.prototype.hasOwnProperty.call(
      (patchTemplate as unknown as jest.Mock).mock.calls[0][0].changedFields,
      'tasks.0.name',
    )).toBe(false);
  });
});

describe('useTemplateForm reference cleanup', () => {
  beforeEach(() => {
    (patchTemplate as unknown as jest.Mock).mockClear();
  });

  it('cleans stale condition rules synchronously when kickoff fields are removed', () => {
    const template = makeTemplate({
      kickoff: {
        description: '',
        fields: [
          { apiName: 'valid-field', name: 'Valid', order: 1 } as any,
          { apiName: 'removed-field', name: 'Removed', order: 2 } as any,
        ],
      } as any,
      tasks: [
        makeTask({
          conditions: [
            {
              apiName: 'cond-1',
              order: 1,
              action: EConditionAction.StartTask,
              rules: [
                {
                  field: 'valid-field',
                  operator: EConditionOperators.Equal,
                  logicOperation: EConditionLogicOperations.And,
                  predicateApiName: '1',
                } as TConditionRule,
                {
                  field: 'removed-field',
                  operator: EConditionOperators.Equal,
                  logicOperation: EConditionLogicOperations.And,
                  predicateApiName: '2',
                } as TConditionRule,
              ],
            },
          ],
        }),
      ],
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue(
        'kickoff',
        { description: '', fields: [{ apiName: 'valid-field', name: 'Valid', order: 1 }] },
        false,
      );
    });

    const rules = handle!.values.tasks[0].conditions[0].rules;
    expect(rules).toHaveLength(1);
    expect(rules[0].field).toBe('valid-field');
    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('cleans stale performer references synchronously when tasks are removed', () => {
    const deletedTask = makeTask({ apiName: 'task-deleted', uuid: 'uuid-deleted', number: 1 });
    const remainingTask = makeTask({
      apiName: 'task-2',
      uuid: 'uuid-2',
      number: 2,
      rawPerformers: [
        { type: ETaskPerformerType.Manager, sourceId: 'task-deleted', label: 'Manager', apiName: 'perf-1' } as any,
        { type: ETaskPerformerType.User, sourceId: '1', label: 'User', apiName: 'perf-2' } as any,
      ],
    });
    const template = makeTemplate({ tasks: [deletedTask, remainingTask] });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('tasks', [{ ...remainingTask, number: 1 }], false);
    });

    expect(handle!.values.tasks).toHaveLength(1);
    expect(handle!.values.tasks[0].rawPerformers).toHaveLength(1);
    expect(handle!.values.tasks[0].rawPerformers[0].apiName).toBe('perf-2');
    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('preserves flushed Formik edits when kickoff cleanup runs before Redux reinitializes', async () => {
    const template = makeTemplate({
      isActive: true,
      description: 'old',
      kickoff: {
        description: '',
        fields: [
          { apiName: 'valid-field', name: 'Valid', order: 1 } as any,
          { apiName: 'removed-field', name: 'Removed', order: 2 } as any,
        ],
      } as any,
      tasks: [
        makeTask({
          conditions: [
            {
              apiName: 'cond-1',
              order: 1,
              action: EConditionAction.StartTask,
              rules: [
                {
                  field: 'removed-field',
                  operator: EConditionOperators.Equal,
                  logicOperation: EConditionLogicOperations.And,
                  predicateApiName: '1',
                } as TConditionRule,
              ],
            },
          ],
        }),
      ],
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'saved edit', false);
    });
    await flushPersist();

    act(() => {
      handle!.setFieldValue('name', 'unsaved edit', false);
      handle!.setFieldValue(
        'kickoff',
        { description: '', fields: [{ apiName: 'valid-field', name: 'Valid', order: 1 }] },
        false,
      );
    });

    expect(handle!.values.description).toBe('saved edit');
    expect(handle!.values.name).toBe('unsaved edit');
    expect(handle!.values.isActive).toBe(false);
    expect(handle!.values.tasks[0].conditions[0].rules).toHaveLength(0);
  });

  it('preserves flushed Formik edits when full tasks replacement runs before Redux reinitializes', async () => {
    const deletedTask = makeTask({ apiName: 'task-deleted', uuid: 'uuid-deleted', number: 1 });
    const remainingTask = makeTask({
      apiName: 'task-2',
      uuid: 'uuid-2',
      number: 2,
      rawPerformers: [
        { type: ETaskPerformerType.Manager, sourceId: 'task-deleted', label: 'Manager', apiName: 'perf-1' } as any,
      ],
    });
    const template = makeTemplate({
      isActive: true,
      description: 'old',
      tasks: [deletedTask, remainingTask],
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('description', 'saved edit', false);
    });
    await flushPersist();

    act(() => {
      handle!.setFieldValue('name', 'unsaved edit', false);
      handle!.setFieldValue('tasks', [{ ...remainingTask, number: 1 }], false);
    });

    expect(handle!.values.description).toBe('saved edit');
    expect(handle!.values.name).toBe('unsaved edit');
    expect(handle!.values.isActive).toBe(false);
    expect(handle!.values.tasks).toHaveLength(1);
    expect(handle!.values.tasks[0].rawPerformers).toHaveLength(0);
  });

  it('does not run reference cleanup when only a task name changes', () => {
    const template = makeTemplate({
      tasks: [
        makeTask({
          name: 'Step with {{missing-field}}',
        }),
      ],
    });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('tasks.0.name', 'Renamed {{missing-field}}', false);
    });

    expect(handle!.values.tasks[0].name).toBe('Renamed {{missing-field}}');
    expect(patchTemplate).not.toHaveBeenCalled();
  });

  it('cleans stale performer references synchronously when a task output field is removed', () => {
    const taskWithOutput = makeTask({
      apiName: 'task-1',
      uuid: 'uuid-1',
      number: 1,
      fields: [{ apiName: 'deleted-output', name: 'Output', order: 1 } as any],
    });
    const dependentTask = makeTask({
      apiName: 'task-2',
      uuid: 'uuid-2',
      number: 2,
      rawPerformers: [
        { type: ETaskPerformerType.OutputUser, sourceId: 'deleted-output', label: 'Output', apiName: 'perf-1' } as any,
        { type: ETaskPerformerType.User, sourceId: '1', label: 'User', apiName: 'perf-2' } as any,
      ],
    });
    const template = makeTemplate({ tasks: [taskWithOutput, dependentTask] });
    let handle: ISpyHandle | null = null;

    render(<TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />);

    act(() => {
      handle!.setFieldValue('tasks.0.fields', [], false);
    });

    expect(handle!.values.tasks[1].rawPerformers).toHaveLength(1);
    expect(handle!.values.tasks[1].rawPerformers[0].apiName).toBe('perf-2');
    expect(patchTemplate).not.toHaveBeenCalled();
  });
});

describe('useTemplateSaveRetry', () => {
  beforeEach(() => {
    mockDispatch.mockClear();
    (patchTemplate as unknown as jest.Mock).mockClear();
    (saveTemplate as unknown as jest.Mock).mockClear();
  });

  function SaveRetryHarness({
    initialTemplate,
    onReady,
  }: {
    initialTemplate: ITemplate;
    onReady(retry: () => void, setFieldValue: (field: string, value: unknown, shouldValidate?: boolean) => void): void;
  }) {
    const { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef } = useTemplateForm(initialTemplate);

    const RetrySpy: React.FC = () => {
      const { setFieldValue: contextSetFieldValue } = useTemplateField();
      const retryFailedSave = useTemplateSaveRetry();
      onReady(retryFailedSave, contextSetFieldValue);
      return null;
    };

    return (
      <TemplateForm
        formik={formik}
        setFieldValue={setFieldValue}
        setValues={setValues}
        dirtyRef={dirtyRef}
        pendingUserEditsRef={pendingUserEditsRef}
        persistBaselineSyncRef={persistBaselineSyncRef}
      >
        <RetrySpy />
      </TemplateForm>
    );
  }

  it('flushes pending Formik edits through patchTemplate instead of saveTemplate', () => {
    const template = makeTemplate({ isActive: true, name: 'Original' });
    let retryFailedSave: (() => void) | null = null;
    let editField: ((field: string, value: unknown, shouldValidate?: boolean) => void) | null = null;

    render(
      <SaveRetryHarness
        initialTemplate={template}
        onReady={(retry, setFieldValue) => {
          retryFailedSave = retry;
          editField = setFieldValue;
        }}
      />,
    );

    act(() => {
      editField!('name', 'Retry edit', false);
    });

    act(() => {
      retryFailedSave!();
    });

    expect(saveTemplate).not.toHaveBeenCalled();
    expect(mockDispatch).toHaveBeenCalledWith(setTemplateStatus(ETemplateStatus.Saving));
    expect(patchTemplate).toHaveBeenCalledWith({
      changedFields: { name: 'Retry edit', isActive: false },
      onSuccess: expect.any(Function),
      onFailed: expect.any(Function),
    });
  });

  it('retries the Redux snapshot when Formik has no unflushed edits', () => {
    const template = makeTemplate({ isActive: true, name: 'Original' });
    let retryFailedSave: (() => void) | null = null;

    render(
      <SaveRetryHarness
        initialTemplate={template}
        onReady={(retry) => { retryFailedSave = retry; }}
      />,
    );

    act(() => {
      retryFailedSave!();
    });

    expect(patchTemplate).not.toHaveBeenCalled();
    expect(mockDispatch).toHaveBeenCalledTimes(1);
    expect(saveTemplate).toHaveBeenCalled();
  });

  it('retries pending Formik edits after an autosave failure instead of saveTemplate', async () => {
    const template = makeTemplate({ isActive: true, name: 'Original' });
    let retryFailedSave: (() => void) | null = null;
    let editField: ((field: string, value: unknown, shouldValidate?: boolean) => void) | null = null;

    render(
      <SaveRetryHarness
        initialTemplate={template}
        onReady={(retry, setFieldValue) => {
          retryFailedSave = retry;
          editField = setFieldValue;
        }}
      />,
    );

    act(() => {
      editField!('name', 'Retry edit', false);
    });

    await flushPersist({ confirmSuccess: false });

    act(() => {
      const calls = (patchTemplate as unknown as jest.Mock).mock.calls;
      const lastCall = calls[calls.length - 1];
      lastCall![0].onFailed();
    });

    expect(patchTemplate).toHaveBeenCalledTimes(1);

    mockDispatch.mockClear();
    (patchTemplate as unknown as jest.Mock).mockClear();

    act(() => {
      retryFailedSave!();
    });

    expect(saveTemplate).not.toHaveBeenCalled();
    expect(patchTemplate).toHaveBeenCalledWith({
      changedFields: { name: 'Retry edit', isActive: false },
      onSuccess: expect.any(Function),
      onFailed: expect.any(Function),
    });
  });

  it('retries a failed activation with isActive true', () => {
    const template = makeTemplate({ isActive: false, name: 'Original' });
    let retryFailedSave: (() => void) | null = null;
    let persist: Pick<ISpyHandle, 'consumePendingChanges' | 'revertConsumedChanges'> | null = null;

    function ActivationRetryHarness() {
      const { formik, setFieldValue, setValues, dirtyRef, pendingUserEditsRef, persistBaselineSyncRef } = useTemplateForm(template);

      const RetrySpy: React.FC = () => {
        retryFailedSave = useTemplateSaveRetry();
        persist = useTemplatePersist();
        return null;
      };

      return (
        <TemplateForm
          formik={formik}
          setFieldValue={setFieldValue}
          setValues={setValues}
          dirtyRef={dirtyRef}
          pendingUserEditsRef={pendingUserEditsRef}
          persistBaselineSyncRef={persistBaselineSyncRef}
        >
          <RetrySpy />
        </TemplateForm>
      );
    }

    render(<ActivationRetryHarness />);

    act(() => {
      persist!.consumePendingChanges({ isActive: true });
      persist!.revertConsumedChanges();
    });

    mockDispatch.mockClear();
    (patchTemplate as unknown as jest.Mock).mockClear();

    act(() => {
      retryFailedSave!();
    });

    expect(saveTemplate).not.toHaveBeenCalled();
    expect(patchTemplate).toHaveBeenCalledWith({
      changedFields: { isActive: true },
      onSuccess: expect.any(Function),
      onFailed: expect.any(Function),
    });
  });
});

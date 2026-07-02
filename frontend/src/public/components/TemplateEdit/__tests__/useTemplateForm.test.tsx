/// <reference types="jest" />
import * as React from 'react';
import { act, render } from '@testing-library/react';

import {
  ITemplate,
  ITemplateTask,
  ETaskPerformerType,
} from '../../../types/template';
import { EConditionAction, EConditionOperators, EConditionLogicOperations, TConditionRule } from '../TaskForm/Conditions/types';
import { TemplateForm, useTemplateField, useTemplateForm, useTemplatePersist } from '../useTemplateForm';
import { patchTemplate } from '../../../redux/actions';

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(() => jest.fn()),
  connect: () => (component: unknown) => component,
}));

jest.mock('../../../redux/actions', () => ({
  ...jest.requireActual('../../../redux/actions'),
  patchTemplate: jest.fn((payload: unknown) => ({ type: 'PATCH_TEMPLATE', payload })),
}));

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

interface ISpyHandle {
  values: ITemplate;
  setFieldValue: (field: string, value: unknown, shouldValidate?: boolean) => void;
  consumePendingChanges: () => Partial<ITemplate>;
  confirmConsumedChanges: () => void;
  revertConsumedChanges: () => void;
  abandonPendingChanges: () => void;
}

// Drain the persist provider's `setTimeout(0)` flush plus the follow-up tick it
// schedules when it mirrors the saga's `isActive` deactivation, so no React
// state update leaks outside `act`.
const flushPersist = () =>
  act(async () => {
    await new Promise((resolve) => { setTimeout(resolve, 0); });
    await new Promise((resolve) => { setTimeout(resolve, 0); });
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
    // and its own effect, but neither setTimeout(0) flush is allowed to fire
    // until both have landed. This is the scenario the persist provider's
    // effect cleanup is meant to handle: the first effect's cleanup must not
    // swallow the second edit.
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

    expect(patchTemplate).not.toHaveBeenCalled();
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
    onReady,
  }: {
    currentTemplate: ITemplate;
    onReady(result: ReturnType<typeof useTemplateForm>): void;
  }) {
    const result = useTemplateForm(currentTemplate);
    onReady(result);
    return null;
  }

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

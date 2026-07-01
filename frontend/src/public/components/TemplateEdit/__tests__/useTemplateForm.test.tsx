/// <reference types="jest" />
import * as React from 'react';
import { act, render } from '@testing-library/react';

import { ITemplate, ITemplateTask } from '../../../types/template';
import { TemplateForm, useTemplateField, useTemplateForm, useTemplatePersist } from '../useTemplateForm';
import { patchTemplate } from '../../../redux/actions';

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(() => jest.fn()),
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
  const { formik, setFieldValue, setValues, dirtyRef } = useTemplateForm(initialTemplate);

  const Spy: React.FC = () => {
    const { values, setFieldValue: contextSetFieldValue } = useTemplateField();
    const { consumePendingChanges } = useTemplatePersist();
    spy({ values, setFieldValue: contextSetFieldValue, consumePendingChanges });
    return null;
  };

  return (
    <TemplateForm formik={formik} setFieldValue={setFieldValue} setValues={setValues} dirtyRef={dirtyRef}>
      <Spy />
    </TemplateForm>
  );
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

    await flushPersist();

    expect(handle!.values.isActive).toBe(false);
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

    expect(pendingChanges).toEqual({ owners });
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

  it('does not dispatch patchTemplate on unmount when pending edits were not flushed', async () => {
    const template = makeTemplate({ isActive: true, description: 'old' });
    let handle: ISpyHandle | null = null;

    const { unmount } = render(
      <TemplateFormHarness initialTemplate={template} spy={(h) => { handle = h; }} />,
    );

    act(() => {
      handle!.setFieldValue('description', 'discarded edit', false);
    });

    unmount();

    await flushPersist();

    expect(patchTemplate).not.toHaveBeenCalled();
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

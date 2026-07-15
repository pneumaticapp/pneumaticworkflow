/// <reference types="jest" />
import { createElement } from 'react';
import { act, render } from '@testing-library/react';
import { FormikProps } from 'formik';

import { ITemplate, ITemplateTask } from '../../../types/template';
import { useTemplateEditTasks } from '../useTemplateEditTasks';
import { intlMock } from '../../../__stubs__/intlMock';

const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
  apiName: 'task-1',
  number: 1,
  name: 'Step 1',
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
});

const makeTemplate = (tasks: ITemplateTask[]): ITemplate =>
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
    tasks,
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: tasks.length,
    performersCount: 0,
  }) as ITemplate;

describe('useTemplateEditTasks', () => {
  it('merges delay edits onto the current Formik task snapshot', () => {
    const staleTask = makeTask({ name: 'Old name', delay: null });
    const liveTask = makeTask({ name: 'Edited in form', delay: null });
    const setFieldValue = jest.fn();
    let editDelay: ((delay: string) => void) | null = null;

    function Harness() {
      const { getTaskListItem } = useTemplateEditTasks({
        authUser: { account: { id: 1 } } as any,
        formik: { values: makeTemplate([liveTask]) } as FormikProps<ITemplate>,
        setFieldValue,
        users: [],
        accessConditions: true,
        formatMessage: intlMock.formatMessage,
        isSubscribed: true,
      });

      editDelay = getTaskListItem(staleTask, 0, [liveTask]).editDelay;
      return null;
    }

    render(createElement(Harness));

    act(() => {
      editDelay!('2d');
    });

    expect(setFieldValue).toHaveBeenCalledWith(
      'tasks',
      [expect.objectContaining({ uuid: 'uuid-1', name: 'Edited in form', delay: '2d' })],
      false,
    );
  });

  it('keeps a stable openTask reference and does not re-open an already opened task', () => {
    const task = makeTask();
    const setFieldValue = jest.fn();
    const openTaskRefs: Array<(taskUUID?: string) => void> = [];

    function Harness() {
      const { openTask } = useTemplateEditTasks({
        authUser: { account: { id: 1 } } as any,
        formik: { values: makeTemplate([task]) } as FormikProps<ITemplate>,
        setFieldValue,
        users: [],
        accessConditions: true,
        formatMessage: intlMock.formatMessage,
        isSubscribed: true,
      });

      openTaskRefs.push(openTask);
      return null;
    }

    const { rerender } = render(createElement(Harness));

    act(() => {
      openTaskRefs[0]!(task.uuid);
    });

    rerender(createElement(Harness));

    expect(openTaskRefs[0]).toBe(openTaskRefs[1]);

    act(() => {
      openTaskRefs[1]!(task.uuid);
    });
  });
});

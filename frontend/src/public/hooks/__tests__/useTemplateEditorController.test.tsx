import * as React from 'react';
import { act, render } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { IUseTemplateEditorControllerOptions, useTemplateEditorController } from '../useTemplateEditorController';
import { ITemplateEditorController } from '../../components/TemplateEdit/types';
import { ITemplateClient, ITemplateTaskClient } from '../../types/template';
import { ETemplateStatus, IAuthUser } from '../../types/redux';
import { cleanTemplateReferences } from '../../utils/template';

jest.mock('throttle-debounce', () => ({
  debounce: (_timeout: number, callback: () => void) => callback,
}));
jest.mock('../../utils/template', () => ({
  cleanTemplateReferences: jest.fn((template: ITemplateClient) => template),
}));
jest.mock('../../components/TemplateEdit/utils/createTemplateTask', () => ({
  createTemplateTask: jest.fn(
    ({ overrides }: { overrides?: Partial<ITemplateTaskClient> }): ITemplateTaskClient =>
      ({
        uuid: 'new-uuid',
        apiName: 'new-task',
        number: 1,
        name: 'New Step',
        delay: null,
        fields: [],
        fieldsets: [],
        conditions: [],
        ...overrides,
      }) as unknown as ITemplateTaskClient,
  ),
}));

const task = {
  uuid: 'task-uuid',
  apiName: 'task-1',
  number: 1,
  name: 'Task 1',
  delay: null,
  fields: [],
  fieldsets: [],
  conditions: [],
} as unknown as ITemplateTaskClient;

const template = {
  id: 1,
  name: 'Template',
  isActive: true,
  tasks: [task],
  kickoff: { description: '', fields: [], fieldsets: [] },
} as unknown as ITemplateClient;

let controller: ITemplateEditorController | null = null;

const Probe = (options: IUseTemplateEditorControllerOptions) => {
  controller = useTemplateEditorController(options);
  return null;
};

const createOptions = (
  overrides: Partial<IUseTemplateEditorControllerOptions> = {},
): IUseTemplateEditorControllerOptions => ({
  template,
  authUser: { id: 1 } as IAuthUser,
  accessConditions: true,
  shouldOpenFirstTask: false,
  selectedTaskApiName: null,
  saveTemplate: jest.fn(),
  setTemplate: jest.fn(),
  setTemplateStatus: jest.fn(),
  setSelectedTask: jest.fn(),
  ...overrides,
});

const renderController = (options: IUseTemplateEditorControllerOptions) =>
  render(
    <IntlProvider locale="en">
      <Probe {...options} />
    </IntlProvider>,
  );

describe('useTemplateEditorController', () => {
  beforeEach(() => {
    controller = null;
    jest.clearAllMocks();
  });

  it('should append a task through the shared structural update pipeline', () => {
    const options = createOptions();
    renderController(options);

    act(() => controller?.addTask());

    expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
    expect(options.setTemplateStatus).toHaveBeenCalledWith(ETemplateStatus.Saving);
    expect(options.setTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        isActive: false,
        tasks: [
          task,
          expect.objectContaining({
            apiName: 'new-task',
            number: 2,
            name: 'New Step 2',
          }),
        ],
      }),
    );
    expect(options.saveTemplate).toHaveBeenCalledTimes(1);
  });

  it('should keep line expansion state inside the shared container controller', () => {
    const options = createOptions();
    renderController(options);

    act(() => controller?.toggleTask(task.uuid));

    expect(controller?.openedTasks[task.uuid]).toBe(true);
  });

  it('should clear graph selection when the selected task is removed', () => {
    const options = createOptions({ selectedTaskApiName: task.apiName });
    renderController(options);

    act(() => controller?.removeTask(task));

    expect(options.setSelectedTask).toHaveBeenCalledWith(null);
    expect(options.setTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        tasks: [expect.objectContaining({ apiName: 'new-task' })],
      }),
    );
  });

  it('should update kickoff through the same normalized structural pipeline', () => {
    const options = createOptions();
    const kickoff = { description: 'Updated', fields: [], fieldsets: [] };
    renderController(options);

    act(() => controller?.setKickoff(kickoff));

    expect(cleanTemplateReferences).toHaveBeenCalledTimes(1);
    expect(options.setTemplate).toHaveBeenCalledWith(expect.objectContaining({ kickoff, isActive: false }));
  });
});

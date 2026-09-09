import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { GRAPH_SHOWCASE_TEMPLATE } from '../../TemplateGraphEditor/fixtures/graphShowcaseTemplate';
import { ITemplateEditorController } from '../../types';
import { TemplateGraphEditorView } from '../TemplateGraphEditorView';

jest.mock('../../TemplateGraphEditor', () => ({
  TemplateGraphEditor: ({ onTaskDelete }: { onTaskDelete(apiName: string): void }) => (
    <button type="button" onClick={() => onTaskDelete('task-linear')}>
      Delete graph task
    </button>
  ),
  GraphTaskEditorPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('../../KickoffRedux', () => ({
  KickoffReduxContainer: () => null,
}));

jest.mock('../../TaskForm', () => ({
  WorkflowTaskFormContainer: () => null,
}));

const createController = (): ITemplateEditorController => ({
  sortedTasks: GRAPH_SHOWCASE_TEMPLATE.tasks,
  openedTasks: {},
  openedDelays: {},
  setKickoff: jest.fn(),
  addTask: jest.fn(),
  addTaskBefore: jest.fn(),
  addTaskFromGraph: jest.fn(),
  removeTask: jest.fn(),
  cloneTask: jest.fn(),
  moveTask: jest.fn(),
  addDelay: jest.fn(),
  editDelay: jest.fn(),
  deleteDelay: jest.fn(),
  toggleTask: jest.fn(),
  toggleDelay: jest.fn(),
});

describe('TemplateGraphEditorView', () => {
  it('should remove the graph task resolved by apiName', () => {
    const controller = createController();

    render(
      <TemplateGraphEditorView
        template={GRAPH_SHOWCASE_TEMPLATE}
        users={[]}
        selectedTaskApiName={null}
        controller={controller}
        selectTask={jest.fn()}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Delete graph task' }));

    expect(controller.removeTask).toHaveBeenCalledWith(expect.objectContaining({ apiName: 'task-linear' }));
  });

  it('should ignore an unknown graph task apiName', () => {
    const controller = createController();
    controller.sortedTasks = [];

    render(
      <TemplateGraphEditorView
        template={GRAPH_SHOWCASE_TEMPLATE}
        users={[]}
        selectedTaskApiName={null}
        controller={controller}
        selectTask={jest.fn()}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Delete graph task' }));

    expect(controller.removeTask).not.toHaveBeenCalled();
  });
});

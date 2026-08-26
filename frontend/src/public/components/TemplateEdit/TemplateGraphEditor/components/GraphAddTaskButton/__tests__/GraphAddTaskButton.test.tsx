import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { configure } from '@testing-library/react';

import { GraphAddTaskButton } from '../GraphAddTaskButton';

configure({ testIdAttribute: 'data-test-id' });

describe('GraphAddTaskButton', () => {
  it('should emit a continue intent and stop the click from bubbling', () => {
    const onAddTask = jest.fn();
    const onParentClick = jest.fn();

    render(
      <div onClick={onParentClick}>
        <GraphAddTaskButton
          intent={{ kind: 'continue', afterId: 'task-a' }}
          onAddTask={onAddTask}
        />
      </div>,
    );

    userEvent.click(screen.getByTestId('graph-add-task'));

    expect(onAddTask).toHaveBeenCalledWith({ kind: 'continue', afterId: 'task-a' });
    expect(onParentClick).not.toHaveBeenCalled();
    expect(screen.getByTestId('graph-add-task')).toHaveAttribute('data-kind', 'continue');
  });

  it('should emit an insert intent', () => {
    const onAddTask = jest.fn();

    render(
      <GraphAddTaskButton
        intent={{ kind: 'insert', afterId: 'task-a', beforeId: 'task-b' }}
        onAddTask={onAddTask}
      />,
    );

    userEvent.click(screen.getByRole('button', { name: 'Add task' }));

    expect(onAddTask).toHaveBeenCalledWith({
      kind: 'insert',
      afterId: 'task-a',
      beforeId: 'task-b',
    });
  });
});

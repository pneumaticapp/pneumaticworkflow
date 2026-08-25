import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReactFlowProvider } from 'reactflow';
import { configure } from '@testing-library/react';

import { EExtraFieldType, ETaskPerformerType, ITemplateTaskClient } from '../../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../../TaskForm/Conditions';
import { TaskNode } from '../TaskNode';
import { EMPTY_CONNECTED_HANDLES } from '../../../utils/applyConnectedHandles';

configure({ testIdAttribute: 'data-test-id' });

function createTask(overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient {
  return {
    apiName: 'task-1',
    name: 'Prepare Layout For Development',
    description: '',
    number: 1,
    requireCompletionByAll: false,
    skipForStarter: false,
    fields: [
      {
        apiName: 'field-1',
        name: 'Layout',
        type: EExtraFieldType.String,
        order: 0,
        userId: null,
        groupId: null,
      },
    ],
    fieldsets: [],
    rawPerformers: [
      {
        label: 'Alex',
        type: ETaskPerformerType.User,
        sourceId: '1',
        apiName: 'performer-1',
      },
    ],
    delay: null,
    rawDueDate: createEmptyTaskDueDate(),
    conditions: [
      {
        apiName: 'condition-1',
        order: 1,
        action: EConditionAction.StartTask,
        rules: [
          {
            ruleApiName: 'rule-1',
            predicateApiName: 'predicate-1',
            field: 'field-1',
            operator: EConditionOperators.Exist,
            logicOperation: EConditionLogicOperations.And,
          },
        ],
      },
    ],
    uuid: 'uuid-1',
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  };
}

const renderTaskNode = (task: ITemplateTaskClient, onEdit = jest.fn()) =>
  render(
    <ReactFlowProvider>
      <TaskNode
        id={task.apiName}
        type="task"
        data={{ task, isSelected: false, onEdit }}
        selected={false}
        isConnectable
        dragging={false}
        zIndex={1}
        xPos={0}
        yPos={0}
      />
    </ReactFlowProvider>,
  );

describe('TaskNode', () => {
  it('should render task label, title and counts from the mockup', () => {
    renderTaskNode(createTask());

    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Prepare Layout For Development')).toBeInTheDocument();
    expect(screen.getByText('1 performer')).toBeInTheDocument();
    expect(screen.getByText('1 field')).toBeInTheDocument();
    expect(screen.getByText('1 condition')).toBeInTheDocument();
  });

  it('should hide zero-count meta items', () => {
    renderTaskNode(createTask({ rawPerformers: [], fields: [], conditions: [] }));

    expect(screen.queryByText(/performer/)).not.toBeInTheDocument();
    expect(screen.queryByText(/field/)).not.toBeInTheDocument();
    expect(screen.queryByText(/condition/)).not.toBeInTheDocument();
  });

  it('should keep all handles mounted so edges can switch sides', () => {
    const { container } = renderTaskNode(createTask());

    expect(container.querySelectorAll('.react-flow__handle')).toHaveLength(8);
    expect(container.querySelectorAll('.react-flow__handle-top')).toHaveLength(2);
    expect(container.querySelectorAll('.react-flow__handle-bottom')).toHaveLength(2);
    expect(container.querySelectorAll('.react-flow__handle-left')).toHaveLength(2);
    expect(container.querySelectorAll('.react-flow__handle-right')).toHaveLength(2);
  });

  it('should mark only connected handles as visible', () => {
    const { container } = render(
      <ReactFlowProvider>
        <TaskNode
          id="task-1"
          type="task"
          data={{
            task: createTask(),
            isSelected: false,
            onEdit: jest.fn(),
            handles: {
              ...EMPTY_CONNECTED_HANDLES,
              hasSourceRight: true,
            },
          }}
          selected={false}
          isConnectable
          dragging={false}
          zIndex={1}
          xPos={0}
          yPos={0}
        />
      </ReactFlowProvider>,
    );

    expect(container.querySelectorAll('.react-flow__handle')).toHaveLength(8);
    const idleHandles = Array.from(container.querySelectorAll('.react-flow__handle'))
      .filter((element) => element.className.includes('handle--idle'));
    const visibleRight = Array.from(container.querySelectorAll('.react-flow__handle-right'))
      .find((element) => !element.className.includes('handle--idle'));

    expect(idleHandles).toHaveLength(7);
    expect(visibleRight).toBeTruthy();
  });

  it('should call onEdit when the kebab is clicked', () => {
    const onEdit = jest.fn();
    renderTaskNode(createTask(), onEdit);

    userEvent.click(screen.getByTestId('graph-node-edit'));

    expect(onEdit).toHaveBeenCalledWith('task-1');
  });

  it('should mark the card as selected', () => {
    render(
      <ReactFlowProvider>
        <TaskNode
          id="task-1"
          type="task"
          data={{ task: createTask(), isSelected: true, onEdit: jest.fn() }}
          selected
          isConnectable
          dragging={false}
          zIndex={1}
          xPos={0}
          yPos={0}
        />
      </ReactFlowProvider>,
    );

    expect(screen.getByTestId('graph-task-node')).toHaveAttribute('data-selected', 'true');
  });
});

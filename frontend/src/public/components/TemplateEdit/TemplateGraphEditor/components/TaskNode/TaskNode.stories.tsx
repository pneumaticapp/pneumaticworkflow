import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { ReactFlowProvider } from 'reactflow';

import { EExtraFieldType, ETaskPerformerType, ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { TaskNode } from './TaskNode';

const task: ITemplateTaskClient = {
  apiName: 'task-1',
  name: 'Prepare Layout For Development',
  description: '',
  number: 1,
  requireCompletionByAll: false,
  skipForStarter: false,
  fields: Array.from({ length: 6 }, (_, index) => ({
    apiName: `field-${index}`,
    name: `Field ${index + 1}`,
    type: EExtraFieldType.String,
    order: index,
    userId: null,
    groupId: null,
  })),
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
      apiName: 'condition-start',
      order: 1,
      action: EConditionAction.StartTask,
      rules: [
        {
          ruleApiName: 'rule-start',
          predicateApiName: 'predicate-start',
          field: 'field-0',
          operator: EConditionOperators.Exist,
          logicOperation: EConditionLogicOperations.And,
        },
      ],
    },
    {
      apiName: 'condition-skip',
      order: 2,
      action: EConditionAction.SkipTask,
      rules: [
        {
          ruleApiName: 'rule-skip',
          predicateApiName: 'predicate-skip',
          field: 'field-0',
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
};

const meta = {
  title: 'TemplateEdit/TaskNode',
  component: TaskNode,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ReactFlowProvider>
        <Story />
      </ReactFlowProvider>
    ),
  ],
} satisfies Meta<typeof TaskNode>;

export default meta;
type Story = StoryObj<typeof meta>;

const nodeProps = {
  id: 'task-1',
  type: 'task',
  isConnectable: true,
  dragging: false,
  zIndex: 1,
  xPos: 0,
  yPos: 0,
};

export const Default: Story = {
  args: {
    ...nodeProps,
    selected: false,
    data: { task, isSelected: false, onEdit: () => undefined },
  },
};

export const Selected: Story = {
  args: {
    ...nodeProps,
    selected: true,
    data: { task, isSelected: true, onEdit: () => undefined },
  },
};

export const EmptyMeta: Story = {
  args: {
    ...nodeProps,
    selected: false,
    data: {
      task: { ...task, rawPerformers: [], fields: [], conditions: [] },
      isSelected: false,
      onEdit: () => undefined,
    },
  },
};

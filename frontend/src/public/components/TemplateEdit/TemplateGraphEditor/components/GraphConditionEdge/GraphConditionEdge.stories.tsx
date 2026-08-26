import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Position, ReactFlowProvider } from 'reactflow';

import { GraphConditionEdge } from './GraphConditionEdge';

const meta = {
  title: 'TemplateEdit/GraphConditionEdge',
  component: GraphConditionEdge,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ReactFlowProvider>
        <svg width="240" height="160">
          <Story />
        </svg>
      </ReactFlowProvider>
    ),
  ],
} satisfies Meta<typeof GraphConditionEdge>;

export default meta;
type Story = StoryObj<typeof meta>;

const edgeArgs = {
  id: 'edge-1',
  source: 'task-a',
  target: 'task-b',
  sourceX: 120,
  sourceY: 16,
  targetX: 120,
  targetY: 144,
  sourcePosition: Position.Bottom,
  targetPosition: Position.Top,
};

export const Default: Story = {
  args: {
    ...edgeArgs,
    data: { isConditional: false },
  },
};

export const StartAfter: Story = {
  args: {
    ...edgeArgs,
    data: {
      isConditional: false,
      startAfter: ['Prepare layout'],
    },
    style: {
      stroke: 'var(--pneumatic-color-black32)',
    },
  },
};

export const InsertPlus: Story = {
  args: {
    ...edgeArgs,
    data: {
      isConditional: false,
      startAfter: ['Prepare layout'],
      addTaskIntent: { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
      onAddTask: () => undefined,
    },
    style: {
      stroke: 'var(--pneumatic-color-black32)',
    },
  },
};

export const Conditional: Story = {
  args: {
    ...edgeArgs,
    data: {
      isConditional: true,
      summary: 'Client Exists',
    },
    style: {
      stroke: 'var(--pneumatic-color-link)',
      strokeDasharray: '6 4',
    },
  },
};

export const FromTask: Story = {
  args: {
    ...edgeArgs,
    sourceX: 40,
    sourceY: 16,
    targetX: 200,
    targetY: 144,
    data: { pathKind: 'from-task', isConditional: false },
  },
};

export const FromFork: Story = {
  args: {
    ...edgeArgs,
    sourceX: 120,
    sourceY: 16,
    targetX: 40,
    targetY: 144,
    data: { pathKind: 'from-fork', isConditional: false },
  },
};

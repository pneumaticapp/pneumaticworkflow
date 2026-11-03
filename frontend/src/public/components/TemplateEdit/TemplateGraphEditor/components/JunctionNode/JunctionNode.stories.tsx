import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { ReactFlowProvider } from 'reactflow';

import { JunctionNode } from './JunctionNode';

const meta = {
  title: 'TemplateEdit/JunctionNode',
  component: JunctionNode,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ReactFlowProvider>
        <Story />
      </ReactFlowProvider>
    ),
  ],
} satisfies Meta<typeof JunctionNode>;

export default meta;
type Story = StoryObj<typeof meta>;

const nodeProps = {
  id: 'junction-fork-task-a',
  type: 'junction',
  selected: false,
  isConnectable: false,
  dragging: false,
  zIndex: 1,
  xPos: 0,
  yPos: 0,
};

export const Fork: Story = {
  args: {
    ...nodeProps,
    data: { kind: 'fork' },
  },
};

export const Join: Story = {
  args: {
    ...nodeProps,
    id: 'junction-join-task-d',
    data: { kind: 'join' },
  },
};

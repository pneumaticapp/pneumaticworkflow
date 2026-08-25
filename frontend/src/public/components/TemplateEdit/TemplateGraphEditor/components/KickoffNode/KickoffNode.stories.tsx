import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { ReactFlowProvider } from 'reactflow';

import { EExtraFieldType } from '../../../../../types/template';
import { KickoffNode } from './KickoffNode';

const meta = {
  title: 'TemplateEdit/KickoffNode',
  component: KickoffNode,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ReactFlowProvider>
        <Story />
      </ReactFlowProvider>
    ),
  ],
} satisfies Meta<typeof KickoffNode>;

export default meta;
type Story = StoryObj<typeof meta>;

const nodeProps = {
  id: 'kickoff',
  type: 'kickoff',
  selected: false,
  isConnectable: true,
  dragging: false,
  zIndex: 1,
  xPos: 0,
  yPos: 0,
};

export const Default: Story = {
  args: {
    ...nodeProps,
    data: {
      templateName: 'New Template',
      kickoff: {
        description: 'Nullam id ipsum et libero aliquet aliquet. Proin tincidunt vestibulum e....',
        fields: [
          {
            apiName: 'field-1',
            name: 'Client',
            type: EExtraFieldType.String,
            order: 0,
            userId: null,
            groupId: null,
          },
        ],
        fieldsets: [],
      },
    },
  },
};

export const Empty: Story = {
  args: {
    ...nodeProps,
    data: {
      templateName: 'New Template',
      kickoff: {
        description: '',
        fields: [],
        fieldsets: [],
      },
    },
  },
};

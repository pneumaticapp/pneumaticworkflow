import type { Meta, StoryObj } from '@storybook/react';

import { ConditionEdgeInfo } from './ConditionEdgeInfo';

const meta = {
  title: 'TemplateEdit/ConditionEdgeInfo',
  component: ConditionEdgeInfo,
  tags: ['autodocs'],
} satisfies Meta<typeof ConditionEdgeInfo>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const Conditional: Story = {
  args: {
    isConditional: true,
    summary: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque facilisis odio eu diam efficitur malesuada',
  },
};

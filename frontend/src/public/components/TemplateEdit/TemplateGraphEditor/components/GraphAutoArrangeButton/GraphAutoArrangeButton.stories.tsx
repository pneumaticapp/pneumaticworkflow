import type { Meta, StoryObj } from '@storybook/react';
import { userEvent, within, expect, fn } from '@storybook/test';

import { GraphAutoArrangeButton } from './GraphAutoArrangeButton';

const meta = {
  title: 'TemplateEdit/GraphAutoArrangeButton',
  component: GraphAutoArrangeButton,
  tags: ['autodocs'],
  args: {
    onReset: fn(),
  },
} satisfies Meta<typeof GraphAutoArrangeButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Inactive: Story = {
  args: {
    isActive: false,
  },
};

export const Active: Story = {
  args: {
    isActive: true,
  },
};

export const ResetsLayout: Story = {
  args: {
    isActive: true,
  },
  play: async ({ args, canvasElement }) => {
    const canvas = within(canvasElement);

    await userEvent.click(canvas.getByRole('button', { name: 'Auto-arrange' }));
    await expect(args.onReset).toHaveBeenCalledTimes(1);
  },
};

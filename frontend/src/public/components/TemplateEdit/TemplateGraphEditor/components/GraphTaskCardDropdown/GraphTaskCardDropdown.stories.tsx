import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { fn, userEvent, within } from '@storybook/test';

import { GraphTaskCardDropdown } from './GraphTaskCardDropdown';

const meta = {
  title: 'TemplateEdit/GraphTaskCardDropdown',
  component: GraphTaskCardDropdown,
  tags: ['autodocs'],
  args: {
    onEdit: fn(),
    onDelete: fn(),
  },
  decorators: [
    (Story) => (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '8rem' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof GraphTaskCardDropdown>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Closed: Story = {};

export const Open: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole('button', { name: 'Task actions' }));
  },
};

export const ConfirmDelete: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole('button', { name: 'Task actions' }));
    await userEvent.click(canvas.getByRole('menuitem', { name: 'Delete' }));
  },
};

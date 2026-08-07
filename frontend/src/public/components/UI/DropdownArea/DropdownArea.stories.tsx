import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { DropdownArea } from './DropdownArea';

const meta = {
  title: 'UI/Dropdowns/DropdownArea',
  component: DropdownArea,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Arbitrary content in a dropdown panel — used by "Add guest". Composes `Dropdown` + `DropdownControl`.',
      },
    },
  },
  argTypes: {
    title: { control: 'text' },
    placement: {
      control: 'select',
      options: ['bottom-start', 'bottom-end', 'top-start', 'top-end'],
    },
  },
  args: {
    title: 'Add guest',
    children: (
      <div style={{ width: '28rem' }}>
        <p>Invite an external user by email. They get access to this task only.</p>
      </div>
    ),
  },
} satisfies Meta<typeof DropdownArea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const CustomToggle: Story = {
  args: { toggle: <span>Open custom panel</span> },
};

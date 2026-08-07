import type { Meta, StoryObj } from '@storybook/react';

import { DropdownControl } from './DropdownControl';

const meta = {
  title: 'UI/Dropdowns/DropdownControl',
  component: DropdownControl,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'The compact chip toggle shared by "Add performer", "Add guest" and the `sm` variant of '
          + '`DropdownList`. Regular weight, `black100` text — the same in every context.',
      },
    },
  },
  argTypes: {
    isOpen: { control: 'boolean' },
    title: { control: 'text' },
  },
  args: {
    title: 'Add performer',
    isOpen: false,
  },
} satisfies Meta<typeof DropdownControl>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Open: Story = {
  args: { isOpen: true },
};

export const AddGuest: Story = {
  args: { title: 'Add guest' },
};

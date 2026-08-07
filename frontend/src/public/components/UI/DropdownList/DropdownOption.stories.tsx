import type { Meta, StoryObj } from '@storybook/react';

import { DropdownOption } from './DropdownOption';

const meta = {
  title: 'UI/Dropdowns/DropdownOption',
  component: DropdownOption,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'The shared option label. Used by `DropdownList`, the condition selects and the users dropdown '
          + 'so a selected option reads the same everywhere.',
      },
    },
  },
  argTypes: {
    isSelected: { control: 'boolean' },
    withTooltip: { control: 'boolean' },
    label: { control: 'text' },
  },
  args: {
    label: 'Specific user',
    isSelected: false,
    withTooltip: false,
  },
} satisfies Meta<typeof DropdownOption>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Selected: Story = {
  args: { isSelected: true },
};

export const WithTooltip: Story = {
  args: { withTooltip: true, label: 'A very long option label that gets truncated in the menu' },
};

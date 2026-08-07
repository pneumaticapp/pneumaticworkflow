import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { ETaskListSorting } from '../../../types/tasks';
import { SelectMenu } from './SelectMenu';

const meta = {
  title: 'UI/Dropdowns/SelectMenu',
  component: SelectMenu,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Sorting-style value picker. Composes `Dropdown`.',
      },
    },
  },
  argTypes: {
    withRadio: { control: 'boolean' },
    closeOnSelect: { control: 'boolean' },
    isDisabled: { control: 'boolean' },
    hideSelectedOption: { control: 'boolean' },
  },
  args: {
    values: Object.values(ETaskListSorting),
    activeValue: ETaskListSorting.DateDesc,
    onChange: () => undefined,
    closeOnSelect: true,
    withRadio: false,
    isDisabled: false,
  },
} satisfies Meta<typeof SelectMenu<ETaskListSorting>>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithRadio: Story = {
  args: { withRadio: true },
};

export const Disabled: Story = {
  args: { isDisabled: true },
};

function InteractiveStory() {
  const [sorting, setSorting] = useState(ETaskListSorting.DateDesc);

  return (
    <SelectMenu<ETaskListSorting>
      values={Object.values(ETaskListSorting)}
      activeValue={sorting}
      onChange={setSorting}
      closeOnSelect
    />
  );
}

export const Interactive: Story = { render: () => <InteractiveStory /> };

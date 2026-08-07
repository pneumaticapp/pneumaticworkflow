import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { DropdownList } from './DropdownList';
import { TDropdownOptionBase } from './types';

type TOption = { label: string; value: string };

const OPTIONS: TOption[] = [
  { label: 'Workflow starter', value: 'starter' },
  { label: 'Specific user', value: 'user' },
  { label: 'User group', value: 'group' },
  { label: 'Field value', value: 'field' },
];

const meta = {
  title: 'UI/Dropdowns/DropdownList',
  component: DropdownList,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Value selection for forms. Composes `Dropdown`, so it shares the menu surface, option rows '
          + 'and dismissal behaviour with every other dropdown. Search lives inside the menu at both sizes.',
      },
    },
  },
  argTypes: {
    controlSize: { control: 'inline-radio', options: ['lg', 'sm'] },
    placement: { control: 'inline-radio', options: [undefined, 'left', 'right'] },
    isSearchable: { control: 'boolean' },
    isMulti: { control: 'boolean' },
    isDisabled: { control: 'boolean' },
    isRequired: { control: 'boolean' },
    staticMenu: { control: 'boolean' },
    label: { control: 'text' },
    placeholder: { control: 'text' },
    errorMessage: { control: 'text' },
  },
  args: {
    options: OPTIONS,
    placeholder: 'Select a value',
    controlSize: 'lg',
    isSearchable: false,
    isDisabled: false,
    isRequired: false,
  },
} satisfies Meta<typeof DropdownList<TOption>>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Uncontrolled: the component keeps the selection itself. */
export const Default: Story = {};

export const WithLabel: Story = {
  args: { label: 'Condition field', isRequired: true },
};

export const WithError: Story = {
  args: { label: 'Condition field', errorMessage: 'This field is required' },
};

export const Searchable: Story = {
  args: { isSearchable: true, placeholder: 'Search values' },
};

export const Grouped: Story = {
  args: {
    options: [
      { label: 'System events', options: [{ label: 'Workflow started', value: 'started' }] },
      { label: 'Date fields', options: [{ label: 'Due date', value: 'due' }, { label: 'Start date', value: 'start' }] },
    ],
  },
};

export const Compact: Story = {
  name: 'Compact control (sm)',
  args: { controlSize: 'sm', title: 'Sort by' },
};

export const StaticMenu: Story = {
  name: 'Static menu (no control)',
  args: { staticMenu: true, isSearchable: true },
};

export const Disabled: Story = {
  args: { isDisabled: true, label: 'Condition field' },
};

function ControlledStory() {
  const [value, setValue] = useState<TOption | null>(OPTIONS[0]);

  return (
    <DropdownList<TOption>
      label="Controlled value"
      options={OPTIONS}
      value={value}
      onChange={(option: TDropdownOptionBase) => setValue(option as TOption)}
    />
  );
}

/** Controlled: the consumer owns the selection. */
export const Controlled: Story = { render: () => <ControlledStory /> };

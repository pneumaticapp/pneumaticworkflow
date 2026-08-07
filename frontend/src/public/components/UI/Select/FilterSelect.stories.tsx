import React, { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { FilterSelect } from './FilterSelect';

type TTemplate = { id: number; name: string };

const TEMPLATES: TTemplate[] = [
  { id: 1, name: 'Customer onboarding' },
  { id: 2, name: 'Invoice approval' },
  { id: 3, name: 'Content review' },
];

const meta = {
  title: 'UI/Dropdowns/FilterSelect',
  component: FilterSelect,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Filter control for lists (workflows, tasks). Composes `Dropdown` + `FilterSelectMenu`.',
      },
    },
  },
  argTypes: {
    isMultiple: { control: 'boolean' },
    isSearchShown: { control: 'boolean' },
    isLoading: { control: 'boolean' },
    isDisabled: { control: 'boolean' },
    isWideMenu: { control: 'boolean' },
  },
  args: {
    options: TEMPLATES,
    optionIdKey: 'id',
    optionLabelKey: 'name',
    noValueLabel: 'All templates',
    placeholderText: 'No templates',
    isLoading: false,
    isDisabled: false,
    selectedOption: null,
    resetFilter: () => undefined,
    onChange: () => undefined,
    renderPlaceholder: () => 'All templates',
  },
} satisfies Meta<typeof FilterSelect<'id', 'name', TTemplate>>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithSearch: Story = {
  args: { isSearchShown: true, searchPlaceholder: 'Search templates' },
};

export const Loading: Story = {
  args: { isLoading: true },
};

function MultipleStory() {
  const [selected, setSelected] = useState<(number | string)[]>([]);

  return (
    <FilterSelect<'id', 'name', TTemplate>
      options={TEMPLATES}
      optionIdKey="id"
      optionLabelKey="name"
      isMultiple
      isSearchShown
      selectAllLabel="Select all"
      noValueLabel="All templates"
      placeholderText="No templates"
      searchPlaceholder="Search templates"
      selectedOptions={selected}
      resetFilter={() => setSelected([])}
      onChange={(next: (number | string)[]) => setSelected(next)}
      renderPlaceholder={() => (selected.length ? `${selected.length} selected` : 'All templates')}
    />
  );
}

export const Multiple: Story = { render: () => <MultipleStory /> };

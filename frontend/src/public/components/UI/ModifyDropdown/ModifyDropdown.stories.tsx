import type { Meta, StoryObj } from '@storybook/react';

import { ModifyDropdown } from './ModifyDropdown';
import { EModifyDropdownToggle } from './types';

const noOp = () => undefined;

const meta = {
  title: 'UI/Dropdowns/ModifyDropdown',
  component: ModifyDropdown,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Edit / Clone / Delete action menu. A thin preset over `Dropdown`.',
      },
    },
  },
  argTypes: {
    toggleType: { control: 'inline-radio', options: Object.values(EModifyDropdownToggle) },
  },
  args: {
    editLabel: 'Edit',
    deleteLabel: 'Delete',
    cloneLabel: 'Clone',
    onEdit: noOp,
    onDelete: noOp,
    onClone: noOp,
    toggleType: EModifyDropdownToggle.Modify,
  },
} satisfies Meta<typeof ModifyDropdown>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const MoreToggle: Story = {
  args: { toggleType: EModifyDropdownToggle.More },
};

export const WithoutClone: Story = {
  args: { cloneLabel: undefined },
};

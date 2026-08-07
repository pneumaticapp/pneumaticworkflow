import type { Meta, StoryObj } from '@storybook/react';

import { DropdownButton } from './DropdownButton';

const noOp = () => undefined;

const meta = {
  title: 'UI/Dropdowns/DropdownButton',
  component: DropdownButton,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Ellipsis button with a menu of labelled actions. Composes `Dropdown`.',
      },
    },
  },
  argTypes: {
    isLoading: { control: 'boolean' },
    isDisabled: { control: 'boolean' },
  },
  args: {
    isLoading: false,
    isDisabled: false,
    dropdownOptions: [
      { itemHeaderIntlId: 'general.modify', onClick: noOp },
      { itemHeaderIntlId: 'dropdown.yes', itemDescriptionIntlId: 'dropdown.are-you-sure', onClick: noOp },
    ],
  },
} satisfies Meta<typeof DropdownButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Loading: Story = {
  args: { isLoading: true },
};

export const Disabled: Story = {
  args: { isDisabled: true },
};

import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { Dropdown } from './Dropdown';
import { IDropdownProps } from './types';

const noOp = () => undefined;
const renderToggle: IDropdownProps['renderToggle'] = () => 'Actions';

const meta = {
  title: 'UI/Dropdowns/Dropdown',
  component: Dropdown,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'The single dropdown foundation: popper positioning, outside-click and Escape dismissal, '
          + 'and the shared menu surface. Every other dropdown in the UI kit composes this one.',
      },
    },
  },
  argTypes: {
    direction: {
      control: 'inline-radio',
      options: [undefined, 'right'],
      description: 'Shorthand alignment; `placement` wins when both are set.',
    },
    placement: {
      control: 'select',
      options: ['bottom-start', 'bottom-end', 'top-start', 'top-end', 'right-start', 'left-start'],
    },
    isDisabled: { control: 'boolean' },
    menuPositionFixed: { control: 'boolean' },
  },
  args: {
    renderToggle,
    isDisabled: false,
  },
} satisfies Meta<typeof Dropdown>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    options: [
      { label: 'Edit', onClick: noOp },
      { label: 'Duplicate', onClick: noOp },
    ],
  },
};

export const WithConfirmation: Story = {
  name: 'Destructive option with confirmation',
  args: {
    options: [
      { label: 'Edit', onClick: noOp },
      { label: 'Delete', color: 'red', withUpperline: true, withConfirmation: true, onClick: noOp },
    ],
  },
};

export const WithSubmenu: Story = {
  args: {
    options: [
      { label: 'Move to', subOptions: [{ label: 'Backlog', onClick: noOp }, { label: 'Archive', onClick: noOp }] },
      { label: 'Duplicate', onClick: noOp },
    ],
  },
};

export const CustomContent: Story = {
  args: {
    renderToggle: (isOpen: boolean) => (isOpen ? 'Close panel' : 'Open panel'),
    children: ({ closeDropdown }: { closeDropdown(): void }) => (
      <div style={{ padding: '1.2rem', width: '24rem' }}>
        <p>Any content can live inside the menu.</p>
        <button type="button" onClick={closeDropdown}>Close</button>
      </div>
    ),
  },
};

export const Disabled: Story = {
  args: {
    isDisabled: true,
    options: [{ label: 'Edit', onClick: noOp }],
  },
};

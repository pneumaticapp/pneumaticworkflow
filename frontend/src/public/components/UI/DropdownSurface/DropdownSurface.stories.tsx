import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { DropdownSurface } from './DropdownSurface';

const meta = {
  title: 'UI/Dropdowns/DropdownSurface',
  component: DropdownSurface,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'The menu panel itself — padding, radius and shadow. Every dropdown menu renders on this surface, '
          + 'which is what makes the condition selects and the action menus look identical.',
      },
    },
  },
  args: {
    children: (
      <div style={{ width: '24rem' }}>
        <div style={{ padding: '0.6rem 1.2rem' }}>First option</div>
        <div style={{ padding: '0.6rem 1.2rem' }}>Second option</div>
      </div>
    ),
  },
} satisfies Meta<typeof DropdownSurface>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

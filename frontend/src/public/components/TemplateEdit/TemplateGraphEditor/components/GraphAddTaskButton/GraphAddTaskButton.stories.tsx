import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { GraphAddTaskButton } from './GraphAddTaskButton';

const meta = {
  title: 'TemplateEdit/GraphAddTaskButton',
  component: GraphAddTaskButton,
  tags: ['autodocs'],
} satisfies Meta<typeof GraphAddTaskButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Continue: Story = {
  args: {
    intent: { kind: 'continue', afterId: 'task-a' },
    onAddTask: () => undefined,
  },
};

export const Insert: Story = {
  args: {
    intent: { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
    onAddTask: () => undefined,
  },
};

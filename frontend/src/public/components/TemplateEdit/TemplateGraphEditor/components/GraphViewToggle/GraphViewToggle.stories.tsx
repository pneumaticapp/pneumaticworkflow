import type { Meta, StoryObj } from '@storybook/react';
import { userEvent, within, expect } from '@storybook/test';

import { GraphViewToggle } from './GraphViewToggle';
import { EGraphViewMode } from '../../types';

const meta = {
  title: 'TemplateEdit/GraphViewToggle',
  component: GraphViewToggle,
  tags: ['autodocs'],
} satisfies Meta<typeof GraphViewToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  parameters: {
    store: {
      templateGraphView: {
        viewMode: EGraphViewMode.List,
        selectedTaskApiName: null,
      },
    },
  },
};

export const Graph: Story = {
  parameters: {
    store: {
      templateGraphView: {
        viewMode: EGraphViewMode.Graph,
        selectedTaskApiName: null,
      },
    },
  },
};

export const SwitchToGraph: Story = {
  parameters: {
    store: {
      templateGraphView: {
        viewMode: EGraphViewMode.List,
        selectedTaskApiName: null,
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const graphButton = canvas.getByRole('button', { name: 'Graph' });

    await userEvent.click(graphButton);
    await expect(graphButton).toBeInTheDocument();
  },
};

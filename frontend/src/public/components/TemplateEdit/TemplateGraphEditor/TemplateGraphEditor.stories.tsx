import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { GRAPH_SHOWCASE_TEMPLATE } from './fixtures/graphShowcaseTemplate';
import { GRAPH_WEAVE_TEMPLATE } from './fixtures/graphWeaveTemplate';
import { TemplateGraphEditor } from './TemplateGraphEditor';

const meta = {
  title: 'TemplateEdit/TemplateGraphEditor',
  component: TemplateGraphEditor,
  tags: ['autodocs'],
  parameters: { layout: 'fullscreen' },
  decorators: [
    (Story) => (
      <div style={{ width: '100%', height: '100vh' }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof TemplateGraphEditor>;

export default meta;
type Story = StoryObj<typeof meta>;

export const AllVariants: Story = {
  args: {
    template: GRAPH_SHOWCASE_TEMPLATE,
    onTaskEdit: () => undefined,
    onKickoffEdit: () => undefined,
  },
};

export const WeaveConditions: Story = {
  args: {
    template: GRAPH_WEAVE_TEMPLATE,
    onTaskEdit: () => undefined,
    onKickoffEdit: () => undefined,
  },
};

export const PersistentPositions: Story = {
  args: {
    template: {
      ...GRAPH_SHOWCASE_TEMPLATE,
      id: 900001,
    },
    onTaskEdit: () => undefined,
    onKickoffEdit: () => undefined,
  },
};

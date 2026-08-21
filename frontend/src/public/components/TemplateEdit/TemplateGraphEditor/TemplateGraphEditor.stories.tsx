import type { Meta, StoryObj } from '@storybook/react';

import { GRAPH_SHOWCASE_TEMPLATE } from './fixtures/graphShowcaseTemplate';
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

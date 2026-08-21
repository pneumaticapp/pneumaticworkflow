import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { GraphTaskEditorPanel } from './GraphTaskEditorPanel';

const meta = {
  title: 'TemplateEdit/GraphTaskEditorPanel',
  component: GraphTaskEditorPanel,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => (
      <div
        style={{
          minHeight: '40rem',
          background: 'var(--pneumatic-color-black4)',
        }}
      >
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof GraphTaskEditorPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    onClose: () => undefined,
    children: (
      <div>
        <p>Prepare Layout For Development</p>
        <p>Description and fields from TaskForm</p>
      </div>
    ),
  },
};

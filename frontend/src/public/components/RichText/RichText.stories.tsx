import type { Meta, StoryObj } from '@storybook/react';
import * as React from 'react';
import { RichText } from './RichText';
import { EExtraFieldType } from '../../types/template';
import { TTaskVariable } from '../TemplateEdit/types';
import {
  WORKFLOW_STARTER_VARIABLE_API_NAME,
  WORKFLOW_STARTER_VARIABLE_TITLE,
} from '../TemplateEdit/TaskForm/utils/getTaskVariables';

const sampleVariables: TTaskVariable[] = [
  {
    apiName: WORKFLOW_STARTER_VARIABLE_API_NAME,
    title: WORKFLOW_STARTER_VARIABLE_TITLE,
    type: EExtraFieldType.String,
  },
  {
    apiName: 'client-name-3967',
    title: 'Client name',
    type: EExtraFieldType.String,
  },
];

const meta = {
  title: 'Components/RichText',
  component: RichText,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ maxWidth: '40rem', padding: '1rem' }}>
        <Story />
      </div>
    ),
  ],
  argTypes: {
    text: { control: 'text' },
    isMarkdownMode: { control: 'boolean' },
    embedVideos: { control: 'boolean' },
    interactiveChecklists: { control: 'boolean' },
    hideIcon: { control: 'boolean' },
  },
} satisfies Meta<typeof RichText>;

export default meta;
type Story = StoryObj<typeof meta>;

export const PlainText: Story = {
  args: {
    text: 'Some plain text with **bold** and _italic_ formatting.',
    isMarkdownMode: true,
  },
};

export const WithMentionsAndLinks: Story = {
  args: {
    text: 'Hello, [Jyoti Puri|3]! Check out https://pneumatic.app/ or [Pneumatic website](https://pneumatic.app/)',
    isMarkdownMode: true,
  },
};

export const PlainHtml: Story = {
  args: {
    text: '<p>Rendered as raw HTML without markdown parsing.</p>',
    isMarkdownMode: false,
  },
};

export const WithYouTubeVideo: Story = {
  args: {
    text: 'Watch this tutorial: https://www.youtube.com/watch?v=jNQXAC9IVRw',
    isMarkdownMode: true,
    embedVideos: true,
  },
};

export const WithLoomVideo: Story = {
  args: {
    text: 'Screen recording: https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1',
    isMarkdownMode: true,
    embedVideos: true,
  },
};

export const WithoutEmbeddedVideos: Story = {
  args: {
    text: 'Video link as plain anchor: https://www.youtube.com/watch?v=jNQXAC9IVRw',
    isMarkdownMode: true,
    embedVideos: false,
  },
};

export const WithVariables: Story = {
  args: {
    text: 'Started by: {{workflow-starter}}\nClient: {{client-name-3967}}',
    isMarkdownMode: false,
    variables: sampleVariables,
  },
};

export const WithFileAttachment: Story = {
  args: {
    text: '![report\\[Q1\\].pdf](https://example.com/report.pdf "entityType:file")',
    isMarkdownMode: true,
  },
};

export const WithImage: Story = {
  args: {
    text: '![Sample image](https://picsum.photos/400/200 "entityType:image")',
    isMarkdownMode: true,
  },
};

export const WithChecklist: Story = {
  args: {
    text: 'Task checklist:\n[clist:my-list|item-1]Review requirements[/clist]\n[clist:my-list|item-2]Submit for approval[/clist]',
    isMarkdownMode: true,
    interactiveChecklists: false,
  },
};

export const WithInteractiveChecklist: Story = {
  args: {
    text: 'Interactive checklist:\n[clist:my-list|item-1]Review requirements[/clist]\n[clist:my-list|item-2]Submit for approval[/clist]',
    isMarkdownMode: true,
    interactiveChecklists: true,
  },
};

export const EmptyText: Story = {
  args: {
    text: null,
    isMarkdownMode: true,
  },
};

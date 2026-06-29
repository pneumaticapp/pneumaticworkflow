import type { Meta, StoryObj } from '@storybook/react';
import * as React from 'react';
import { RichText } from './RichText';
import {
  createStoryTask,
  InteractiveRichText,
} from './stories/interactiveChecklistStoryUtils';
import { DASHBOARD_VIDEO_URL } from '../../constants/defaultValues';
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

const myListStoryTask = createStoryTask({
  listApiName: 'my-list',
  itemApiNames: ['item-1', 'item-2'],
  checkedItemApiNames: ['item-1'],
});

const onboardingStoryTask = createStoryTask({
  listApiName: 'onboarding',
  itemApiNames: ['step-1', 'step-2', 'step-3', 'step-4', 'step-5'],
  checkedItemApiNames: ['step-1', 'step-2'],
});

export const WithInteractiveChecklist: Story = {
  render: (args) => <InteractiveRichText {...args} task={myListStoryTask} />,
  args: {
    text: 'Interactive checklist:\n[clist:my-list|item-1]Review requirements[/clist]\n[clist:my-list|item-2]Submit for approval[/clist]',
    isMarkdownMode: true,
  },
};

export const EmptyText: Story = {
  args: {
    text: null,
    isMarkdownMode: true,
  },
};

const LONG_MARKDOWN_TEXT = `# RichText — all supported elements

Demonstrates every content type that RichText can render from stored markdown.

## Text formatting

Paragraph with **bold**, _italic_, and \`inline code\`. Line break below (single newline):
Next line in the same block.

## Mentions

Hello, [Alex Karpov|4] and [Jyoti Puri|3] — please loop in [Support Team|12] before sign-off.

## Variables

Client: {{client-name-3967}}. Workflow started by: {{workflow-starter}}.

## Links

Auto-linkified URL: https://pneumatic.app/

Markdown link: [Pneumatic developers docs](https://pneumatic.app/developers)

Link with brackets in label: [click \\[here\\]](https://example.com)

## Image attachment

![Architecture diagram](https://picsum.photos/800/400 "entityType:image")

![Architecture diagram](https://picsum.photos/800/400 "entityType:image")

Inline image in text: before ![inline icon](https://picsum.photos/120/80 "entityType:image") after.

## Uploaded video attachment

![Product walkthrough.mp4](https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4 "attachment_id:42 entityType:video")

## File attachment

![Report\\[Q1\\].pdf](https://example.com/files/report-q1.pdf "attachment_id:17 entityType:file")

Another file: ![Contract.docx](https://example.com/files/contract.docx "entityType:file")

## Embedded external videos (linkify)

YouTube: https://www.youtube.com/watch?v=jNQXAC9IVRw

Loom: https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1

Wistia: ${DASHBOARD_VIDEO_URL}

## Blockquote

> Important: all PII must stay within approved regions. Do not attach raw exports to public channels.

## Unordered list

- First unordered item
- 1966, when designers at Letraset and James Mosley, the librarian at St Bride Printing Library in London, took a 1914 Cicero translation and scrambled it to make dummy text for Letraset's Body Type sheets. It has survived not only many decades, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised thanks to these sheets and more recently with desktop publishing software like Aldus PageMaker and Microsoft Word including
- Second item with **bold** mention [Alex Karpov|4]
  - Nested unordered child
  - Another nested child
  - 1966, when designers at Letraset and James Mosley, the librarian at St Bride Printing Library in London, took a 1914 Cicero translation and scrambled it to make dummy text for Letraset's Body Type sheets. It has survived not only many decades, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised thanks to these sheets and more recently with desktop publishing software like Aldus PageMaker and Microsoft Word including
- Third item with link https://pneumatic.app/help

## Ordered list

1. Collect documents from {{client-name-3967}}
2. Review scope with [Jyoti Puri|3]
3. Publish template update

## Checklist with rich content

[clist:onboarding|step-1]Review kickoff form and confirm owner {{workflow-starter}}[/clist]
[clist:onboarding|step-2]Validate client data for {{client-name-3967}}[/clist]
[clist:onboarding|step-3]Attach architecture screenshot: ![System diagram](https://picsum.photos/640/360 "entityType:image")[/clist]
[clist:onboarding|step-4]Watch training video: https://www.youtube.com/watch?v=jNQXAC9IVRw[/clist]
[clist:onboarding|step-5]Upload signed SOW: ![SOW\\[2026\\].pdf](https://example.com/sow.pdf "entityType:file")[/clist]

---

Final paragraph: mixed content with _italic_, a [help link](https://pneumatic.app/help), variable {{client-name-3967}}, and mention [Support Team|12].
`;

const longMarkdownStoryArgs = {
  text: LONG_MARKDOWN_TEXT,
  isMarkdownMode: true,
  embedVideos: true,
  variables: sampleVariables,
} as const;

export const LongMarkdown: Story = {
  args: {
    ...longMarkdownStoryArgs,
    interactiveChecklists: false,
  },
};

export const LongMarkdownInteractiveChecklists: Story = {
  render: (args) => <InteractiveRichText {...args} task={onboardingStoryTask} />,
  args: {
    ...longMarkdownStoryArgs,
  },
};

export const LongMarkdownTruncated: Story = {
  args: {
    ...longMarkdownStoryArgs,
    interactiveChecklists: false,
    maxLines: 8,
  },
};

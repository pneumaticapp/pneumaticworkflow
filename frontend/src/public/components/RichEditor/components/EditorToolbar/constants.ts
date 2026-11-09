export const TOOLBAR_LABELS = {
  bold: { tooltip: 'editor.bold', aria: 'editor.bold' },
  italic: { tooltip: 'editor.italic', aria: 'editor.italic' },
  orderedList: { tooltip: 'editor.ordered-list', aria: 'editor.ordered-list' },
  unorderedList: { tooltip: 'editor.unordered-list', aria: 'editor.unordered-list' },
  checklist: { tooltip: 'editor.add-checklist-item', aria: 'editor.checklist' },
  link: { tooltip: 'editor.add-link', aria: 'editor.link' },
  attachImage: { tooltip: 'editor.attach-image', aria: 'editor.attach-image' },
  attachVideo: { tooltip: 'editor.attach-video', aria: 'editor.attach-video' },
  attachFile: { tooltip: 'editor.attach-file', aria: 'editor.attach-file' },
} as const;

export const ATTACHMENT_ACCEPT = {
  image: 'image/*',
  video: 'video/*',
} as const;

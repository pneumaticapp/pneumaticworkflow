export const TOOLBAR_LABELS = {
  bold: { tooltip: 'editor.bold', aria: 'Bold' },
  italic: { tooltip: 'editor.italic', aria: 'Italic' },
  orderedList: { tooltip: 'Ordered List', aria: 'Ordered List' },
  unorderedList: { tooltip: 'Unordered List', aria: 'Unordered List' },
  checklist: { tooltip: 'editor.add-checklist-item', aria: 'Checklist' },
  link: { tooltip: 'editor.add-link', aria: 'Link' },
  attachImage: { tooltip: 'Attach Image', aria: 'Attach Image' },
  attachVideo: { tooltip: 'Attach Video', aria: 'Attach Video' },
  attachFile: { tooltip: 'Attach File', aria: 'Attach File' },
} as const;

export const ATTACHMENT_ACCEPT = {
  image: 'image/*',
  video: 'video/*',
} as const;

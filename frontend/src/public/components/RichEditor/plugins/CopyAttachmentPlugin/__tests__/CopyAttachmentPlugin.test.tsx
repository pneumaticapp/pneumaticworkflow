import * as React from 'react';
import { render, waitFor, act } from '@testing-library/react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import {
  COPY_COMMAND,
  CUT_COMMAND,
  $getRoot,
  $createParagraphNode,
  $createTextNode,
  $createRangeSelection,
  $setSelection,
} from 'lexical';
import type { MutableRefObject } from 'react';
import type { LexicalEditor } from 'lexical';
import { CopyAttachmentPlugin } from '../CopyAttachmentPlugin';
import { SetEditorRefPlugin } from '../../SetEditorRefPlugin';
import {
  ImageAttachmentNode,
  $createImageAttachmentNode,
} from '../../../nodes/attachments/ImageAttachmentNode';
import { LEXICAL_NODES } from '../../../nodes';
import { lexicalTheme } from '../../../theme';

interface SerializedNode {
  type: string;
  children?: SerializedNode[];
  [key: string]: unknown;
}

function collectTypes(nodes: SerializedNode[]): string[] {
  const types: string[] = [];
  for (const n of nodes) {
    types.push(n.type);
    if (n.children) types.push(...collectTypes(n.children));
  }
  return types;
}

function findNodeDeep(nodes: SerializedNode[], type: string): SerializedNode | undefined {
  for (const n of nodes) {
    if (n.type === type) return n;
    if (n.children) {
      const found = findNodeDeep(n.children, type);
      if (found) return found;
    }
  }
  return undefined;
}

beforeAll(() => {
  jest
    .spyOn(ImageAttachmentNode.prototype, 'decorate')
    .mockReturnValue(React.createElement('div', { 'data-testid': 'mock-img' }));
});

afterAll(() => {
  jest.restoreAllMocks();
});

const initialConfig = {
  namespace: 'CopyAttachmentTest',
  theme: lexicalTheme,
  nodes: LEXICAL_NODES,
  onError: () => {},
};

function createClipboardEvent(type: 'copy' | 'cut'): ClipboardEvent {
  const stored: Record<string, string> = {};
  const clipboardData = {
    getData: (key: string) => stored[key] ?? '',
    setData: (key: string, val: string) => {
      stored[key] = val;
    },
    clearData: () => {
      Object.keys(stored).forEach((k) => delete stored[k]);
    },
    types: [] as string[],
    files: [] as File[],
    items: [],
    dropEffect: 'none',
    effectAllowed: 'none',
    setDragImage: () => {},
  } as unknown as DataTransfer;

  let defaultPrevented = false;
  return {
    clipboardData,
    type,
    preventDefault: () => {
      defaultPrevented = true;
    },
    get defaultPrevented() {
      return defaultPrevented;
    },
  } as unknown as ClipboardEvent;
}

function TestHarness({
  editorRef,
}: {
  editorRef: MutableRefObject<LexicalEditor | null>;
}): React.ReactElement {
  return (
    <LexicalComposer initialConfig={initialConfig}>
      <RichTextPlugin
        contentEditable={<ContentEditable />}
        ErrorBoundary={LexicalErrorBoundary}
      />
      <SetEditorRefPlugin editorRef={editorRef} />
      <CopyAttachmentPlugin />
    </LexicalComposer>
  );
}

async function setupEditor(): Promise<LexicalEditor> {
  const editorRef = React.createRef<LexicalEditor | null>() as MutableRefObject<LexicalEditor | null>;
  render(<TestHarness editorRef={editorRef} />);
  await waitFor(() => expect(editorRef.current).not.toBeNull());
  return editorRef.current!;
}

function selectAll(editor: LexicalEditor): void {
  editor.update(
    () => {
      const root = $getRoot();
      const firstChild = root.getFirstDescendant();
      const lastChild = root.getLastDescendant();
      if (!firstChild || !lastChild) return;

      const selection = $createRangeSelection();
      selection.anchor.set(firstChild.getKey(), 0, 'text');
      selection.focus.set(
        lastChild.getKey(),
        lastChild.getTextContentSize?.() ?? 0,
        'text',
      );
      $setSelection(selection);
    },
    { discrete: true },
  );
}

function insertContentWithAttachment(editor: LexicalEditor): void {
  editor.update(
    () => {
      const root = $getRoot();
      root.clear();

      const p1 = $createParagraphNode();
      p1.append($createTextNode('before'));
      root.append(p1);

      const p2 = $createParagraphNode();
      const imgNode = $createImageAttachmentNode({
        url: 'https://example.com/test.jpg',
        id: 5214,
        name: 'download-1.jpg',
      });
      p2.append(imgNode);
      root.append(p2);

      const p3 = $createParagraphNode();
      p3.append($createTextNode('after'));
      root.append(p3);
    },
    { discrete: true },
  );
}

describe('CopyAttachmentPlugin', () => {
  it('intercepts COPY_COMMAND when selection contains a decorator node', async () => {
    const editor = await setupEditor();

    act(() => insertContentWithAttachment(editor));
    act(() => selectAll(editor));

    const event = createClipboardEvent('copy');
    let result: boolean | undefined;

    act(() => {
      result = editor.dispatchCommand(COPY_COMMAND, event);
    });

    expect(result).toBe(true);
    expect(event.defaultPrevented).toBe(true);

    const lexicalData = event.clipboardData!.getData('application/x-lexical-editor');
    expect(lexicalData).toBeTruthy();

    const parsed = JSON.parse(lexicalData);
    const allTypes = collectTypes(parsed.nodes ?? []);
    expect(allTypes).toContain('image-attachment');
  });

  it('does NOT intercept COPY_COMMAND when selection has no decorator nodes', async () => {
    const editor = await setupEditor();

    act(() => {
      editor.update(
        () => {
          const root = $getRoot();
          root.clear();
          const p = $createParagraphNode();
          p.append($createTextNode('plain text only'));
          root.append(p);
        },
        { discrete: true },
      );
    });

    act(() => selectAll(editor));

    const event = createClipboardEvent('copy');

    act(() => {
      editor.dispatchCommand(COPY_COMMAND, event);
    });

    expect(event.defaultPrevented).toBe(false);
  });

  it('returns false for null event', async () => {
    const editor = await setupEditor();

    act(() => {
      const result = editor.dispatchCommand(COPY_COMMAND, null);
      expect(result).toBe(false);
    });
  });

  it('intercepts CUT_COMMAND and removes selected content with decorator', async () => {
    const editor = await setupEditor();

    act(() => insertContentWithAttachment(editor));
    act(() => selectAll(editor));

    const event = createClipboardEvent('cut');
    let result: boolean | undefined;

    act(() => {
      result = editor.dispatchCommand(CUT_COMMAND, event);
    });

    expect(result).toBe(true);
    expect(event.defaultPrevented).toBe(true);

    const lexicalData = event.clipboardData!.getData('application/x-lexical-editor');
    expect(lexicalData).toBeTruthy();
    const parsed = JSON.parse(lexicalData);
    const allTypes = collectTypes(parsed.nodes ?? []);
    expect(allTypes).toContain('image-attachment');

    let textAfterCut = '';
    editor.read(() => {
      textAfterCut = $getRoot().getTextContent();
    });
    expect(textAfterCut.trim()).toBe('');
  });

  it('preserves attachment metadata (url, id, name) in clipboard', async () => {
    const editor = await setupEditor();

    act(() => {
      editor.update(
        () => {
          const root = $getRoot();
          root.clear();

          const p1 = $createParagraphNode();
          p1.append($createTextNode('text'));
          root.append(p1);

          const p2 = $createParagraphNode();
          p2.append(
            $createImageAttachmentNode({
              url: 'https://storage.googleapis.com/dev_2932/download-1.jpg',
              id: 5214,
              name: 'download-1.jpg',
            }),
          );
          root.append(p2);

          const p3 = $createParagraphNode();
          p3.append($createTextNode('more text'));
          root.append(p3);
        },
        { discrete: true },
      );
    });

    act(() => selectAll(editor));

    const event = createClipboardEvent('copy');
    act(() => {
      editor.dispatchCommand(COPY_COMMAND, event);
    });

    expect(event.defaultPrevented).toBe(true);

    const lexicalData = event.clipboardData!.getData('application/x-lexical-editor');
    const parsed = JSON.parse(lexicalData);

    const imgNode = findNodeDeep(parsed.nodes ?? [], 'image-attachment');
    expect(imgNode).toBeDefined();
    expect(imgNode!.url).toBe('https://storage.googleapis.com/dev_2932/download-1.jpg');
    expect(imgNode!.id).toBe(5214);
    expect(imgNode!.name).toBe('download-1.jpg');

    const htmlData = event.clipboardData!.getData('text/html');
    expect(htmlData).toBeTruthy();
    expect(htmlData).toContain('data-lexical-image-attachment');
  });
});

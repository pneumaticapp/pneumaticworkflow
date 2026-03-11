import * as React from 'react';
import { render, waitFor } from '@testing-library/react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { PASTE_COMMAND } from 'lexical';
import type { MutableRefObject } from 'react';
import type { LexicalEditor } from 'lexical';
import { PasteAttachmentPlugin } from '../PasteAttachmentPlugin';
import { SetEditorRefPlugin } from '../../SetEditorRefPlugin';
import { LEXICAL_NODES } from '../../../nodes';
import { lexicalTheme } from '../../../theme';

const initialConfig = {
  namespace: 'PasteAttachmentTest',
  theme: lexicalTheme,
  nodes: LEXICAL_NODES,
  onError: () => {},
};

function createPasteEventWithFiles(files: File[]): ClipboardEvent {
  const fileList = Object.assign([...files], { length: files.length }) as unknown as FileList;
  return {
    clipboardData: {
      files: fileList,
      items: [],
    },
  } as unknown as ClipboardEvent;
}

describe('PasteAttachmentPlugin', () => {
  it('calls onPasteFiles when PASTE_COMMAND is dispatched with files in clipboard', async () => {
    const onPasteFiles = jest.fn().mockResolvedValue(undefined);
    const editorRef = React.createRef<LexicalEditor | null>() as MutableRefObject<LexicalEditor | null>;

    render(
      <LexicalComposer initialConfig={initialConfig}>
        <SetEditorRefPlugin editorRef={editorRef} />
        <PasteAttachmentPlugin onPasteFiles={onPasteFiles} />
      </LexicalComposer>,
    );

    await waitFor(() => {
      expect(editorRef.current).not.toBeNull();
    });

    const file = new File(['content'], 'pasted.png', { type: 'image/png' });
    const event = createPasteEventWithFiles([file]);

    const result = editorRef.current!.dispatchCommand(PASTE_COMMAND, event);

    expect(result).toBe(true);
    expect(onPasteFiles).toHaveBeenCalledTimes(1);
    expect(onPasteFiles).toHaveBeenCalledWith([file]);
  });

  it('returns false when clipboard has no files (does not call onPasteFiles)', async () => {
    const onPasteFiles = jest.fn();
    const editorRef = React.createRef<LexicalEditor | null>() as MutableRefObject<LexicalEditor | null>;

    render(
      <LexicalComposer initialConfig={initialConfig}>
        <SetEditorRefPlugin editorRef={editorRef} />
        <PasteAttachmentPlugin onPasteFiles={onPasteFiles} />
      </LexicalComposer>,
    );

    await waitFor(() => {
      expect(editorRef.current).not.toBeNull();
    });

    const event = createPasteEventWithFiles([]);

    const result = editorRef.current!.dispatchCommand(PASTE_COMMAND, event);

    expect(result).toBe(false);
    expect(onPasteFiles).not.toHaveBeenCalled();
  });

  it('passes multiple files to onPasteFiles', async () => {
    const onPasteFiles = jest.fn().mockResolvedValue(undefined);
    const editorRef = React.createRef<LexicalEditor | null>() as MutableRefObject<LexicalEditor | null>;

    render(
      <LexicalComposer initialConfig={initialConfig}>
        <SetEditorRefPlugin editorRef={editorRef} />
        <PasteAttachmentPlugin onPasteFiles={onPasteFiles} />
      </LexicalComposer>,
    );

    await waitFor(() => {
      expect(editorRef.current).not.toBeNull();
    });

    const file1 = new File(['a'], 'a.png', { type: 'image/png' });
    const file2 = new File(['b'], 'b.jpg', { type: 'image/jpeg' });
    const event = createPasteEventWithFiles([file1, file2]);

    editorRef.current!.dispatchCommand(PASTE_COMMAND, event);

    expect(onPasteFiles).toHaveBeenCalledWith([file1, file2]);
  });
});

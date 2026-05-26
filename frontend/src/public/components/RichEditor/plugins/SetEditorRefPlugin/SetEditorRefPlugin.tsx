import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import type { LexicalEditor } from 'lexical';
import type { MutableRefObject } from 'react';
import { useEffect } from 'react';

export interface ISetEditorRefPluginProps {
  editorRef: MutableRefObject<LexicalEditor | null>;
}

export function SetEditorRefPlugin({ editorRef }: ISetEditorRefPluginProps): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    editorRef.current = editor;
    return () => {
      editorRef.current = null;
    };
  }, [editor, editorRef]);

  return null;
}

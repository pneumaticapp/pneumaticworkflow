import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { KEY_ENTER_COMMAND, COMMAND_PRIORITY_CRITICAL } from 'lexical';
import { useEffect } from 'react';

export interface ISubmitOnKeyPluginProps {
  onSubmit: () => void;
}

export function SubmitOnKeyPlugin({ onSubmit }: ISubmitOnKeyPluginProps): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand<KeyboardEvent | null>(
      KEY_ENTER_COMMAND,
      (event) => {
        const isModEnter = event ? event.metaKey || event.ctrlKey : false;
        if (isModEnter) {
          onSubmit();
          return true;
        }
        return false;
      },
      COMMAND_PRIORITY_CRITICAL,
    );
  }, [editor, onSubmit]);

  return null;
}

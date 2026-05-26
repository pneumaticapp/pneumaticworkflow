import { LexicalEditor } from 'lexical';

export function subscribeBlurClose(
  editor: LexicalEditor,
  closeMenu: () => void,
): (() => void) | undefined {
  const rootElement = editor.getRootElement();
  if (!rootElement) return undefined;

  const handleBlur = () => {
    requestAnimationFrame(() => closeMenu());
  };

  rootElement.addEventListener('blur', handleBlur);

  return () => rootElement.removeEventListener('blur', handleBlur);
}

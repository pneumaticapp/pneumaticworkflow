import type { ChangeEvent } from 'react';
import type { IRichEditorProps } from '../types';

export function resolveUploadHandler(
  propHandler: IRichEditorProps['onUploadAttachments'],
  builtInHandler?: (e: ChangeEvent<HTMLInputElement>) => Promise<void>,
): IRichEditorProps['onUploadAttachments'] {
  return propHandler ?? builtInHandler ?? undefined;
}

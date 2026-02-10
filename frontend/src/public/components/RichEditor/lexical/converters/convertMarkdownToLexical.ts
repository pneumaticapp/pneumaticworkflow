import type { LexicalEditor } from 'lexical';
import { $convertFromMarkdownString } from '@lexical/markdown';
import { prepareChecklistsForRendering } from '../../../../utils/checklists/prepareChecklistsForRendering';
import { createMarkdownTransformers } from './transformers';
import type { TTaskVariable } from '../../../TemplateEdit/types';



export function applyMarkdownToEditor(
  editor: LexicalEditor,
  markdown: string,
  options: { tag?: string; templateVariables?: TTaskVariable[] } = {},
): void {
  try {
    const prepared = prepareChecklistsForRendering(markdown);
    const transformers = createMarkdownTransformers(options.templateVariables);

    editor.update(
      () => {
        $convertFromMarkdownString(prepared, transformers);
      },
      { tag: options.tag ?? 'history-merge' },
    );
  } catch (error) {
    console.error('❌ Error loading markdown into editor:', error);
    // Could optionally clear editor or show error state
  }
}

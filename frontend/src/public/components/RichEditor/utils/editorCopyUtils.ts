import { EditorState, ContentState, convertToRaw } from 'draft-js';
import { stateToHTML } from 'draft-js-export-html';
import { getSelectedContent, getContentStateForBlock } from './getSelectedContent';
import { convertDraftToText } from './converters';
import { isSafari } from './isSafari';
import { ECustomEditorEntities } from './types';

export function stripHtmlToText(html: string): string {
  if (typeof document === 'undefined') return '';
  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent?.trim() ?? div.innerText?.trim() ?? '';
}

export function getSelectedContentForCopy(
  editorStateToUse: EditorState,
  selectionToUse: ReturnType<EditorState['getSelection']>,
): ContentState | null {
  const editorStateWithSelection = EditorState.forceSelection(editorStateToUse, selectionToUse);
  let selectedContentState = getSelectedContent(editorStateWithSelection);
  if (!selectedContentState && isSafari()) {
    const selection = editorStateToUse.getSelection();
    const blockKey = selection.getAnchorKey();
    const contentState = editorStateToUse.getCurrentContent();
    const block = contentState.getBlockForKey(blockKey);
    if (block && block.getLength() > 0) {
      const lastChar = block.getCharacterList().get(block.getLength() - 1);
      const entityKey = lastChar.getEntity();
      if (entityKey !== null) {
        try {
          const entity = contentState.getEntity(entityKey);
          if (entity.getType() === ECustomEditorEntities.Variable) {
            selectedContentState = getContentStateForBlock(editorStateToUse, blockKey);
          }
        } catch {
          // ignore
        }
      }
    }
  }
  if (!selectedContentState) return null;
  if (isSafari() && selectedContentState.getPlainText().trim() === '') {
    const blockKey = selectionToUse.getAnchorKey();
    const fullBlock = getContentStateForBlock(editorStateToUse, blockKey);
    if (fullBlock && fullBlock.getPlainText().trim() !== '') {
      selectedContentState = fullBlock;
    }
  }
  return selectedContentState;
}

export function writeContentStateToClipboard(
  selectedContentState: ContentState,
  e: React.ClipboardEvent,
): string {
  let plainTextForClipboard: string;
  let htmlForClipboard: string;
  try {
    const rawContent = convertToRaw(selectedContentState);
    const serializedContent = JSON.stringify(rawContent);
    plainTextForClipboard = convertDraftToText(selectedContentState);
    if (!plainTextForClipboard || plainTextForClipboard.trim() === '') {
      plainTextForClipboard = selectedContentState.getPlainText();
    }
    htmlForClipboard = stateToHTML(selectedContentState);
    const plain = plainTextForClipboard ?? '';
    e.clipboardData.setData('text/plain', plain);
    e.clipboardData.setData('application/json', serializedContent);
    e.clipboardData.setData('text/html', htmlForClipboard);
    if (isSafari() && typeof navigator !== 'undefined' && navigator.clipboard?.write) {
      navigator.clipboard
        .write([
          new ClipboardItem({
            'text/plain': new Blob([plain], { type: 'text/plain' }),
            'text/html': new Blob([htmlForClipboard], { type: 'text/html' }),
          }),
        ])
        .catch(() => {});
    }
  } catch {
    plainTextForClipboard = selectedContentState.getPlainText() ?? '';
    htmlForClipboard = '';
    e.clipboardData.setData('text/plain', plainTextForClipboard);
    if (isSafari() && typeof navigator !== 'undefined' && navigator.clipboard?.write) {
      navigator.clipboard
        .write([
          new ClipboardItem({ 'text/plain': new Blob([plainTextForClipboard], { type: 'text/plain' }) }),
        ])
        .catch(() => {});
    }
  }
  return plainTextForClipboard ?? '';
}

/**
 * Expands start/end offsets to entity boundaries so we never slice through
 * the middle of an entity (variable, mention, etc.). When the user selects
 * only part of a variable, the entire variable is always included in the copy.
 * Prevents broken content and convertDraftToText/convertToRaw failures.
 */
function expandSelectionToEntityBoundaries(
  contentState: any,
  startKey: string,
  endKey: string,
  startOffset: number,
  endOffset: number,
): { startOffset: number; endOffset: number } {
  let expandedStart = startOffset;
  let expandedEnd = endOffset;

  const startBlock = contentState.getBlockForKey(startKey);
  const startCharList = startBlock.getCharacterList();
  if (startOffset < startCharList.size) {
    const entityAtStart = startCharList.get(startOffset).getEntity();
    if (entityAtStart !== null) {
      while (expandedStart > 0 && startCharList.get(expandedStart - 1).getEntity() === entityAtStart) {
        expandedStart -= 1;
      }
    }
  }

  const endBlock = contentState.getBlockForKey(endKey);
  const endCharList = endBlock.getCharacterList();
  const lastSelectedIndex = endOffset - 1;
  if (lastSelectedIndex >= 0 && lastSelectedIndex < endCharList.size) {
    const entityAtEnd = endCharList.get(lastSelectedIndex).getEntity();
    if (entityAtEnd !== null) {
      while (expandedEnd < endCharList.size && endCharList.get(expandedEnd).getEntity() === entityAtEnd) {
        expandedEnd += 1;
      }
    }
  }

  return { startOffset: expandedStart, endOffset: expandedEnd };
}

export const getSelectedContent = (editorState: any) => {
  const contentState = editorState.getCurrentContent();
  const selection = editorState.getSelection();

  if (selection.isCollapsed()) {
    return null;
  }

  const startKey = selection.getStartKey();
  const endKey = selection.getEndKey();
  let startOffset = selection.getStartOffset();
  let endOffset = selection.getEndOffset();

  const expanded = expandSelectionToEntityBoundaries(contentState, startKey, endKey, startOffset, endOffset);
  startOffset = expanded.startOffset;
  endOffset = expanded.endOffset;

  const blockMap = contentState.getBlockMap();
  const selectedBlocks = blockMap
    .skipUntil((_: any, key: any) => key === startKey)
    .takeUntil((_: any, key: any) => key === endKey)
    .concat([[endKey, blockMap.get(endKey)]]);

  const modifiedBlocks = selectedBlocks.map((block: any, key: any) => {
    let text = block.getText();
    let characterList = block.getCharacterList();

    if (key === startKey && key === endKey) {
      text = text.slice(startOffset, endOffset);
      characterList = characterList.slice(startOffset, endOffset);
    } else if (key === startKey) {
      text = text.slice(startOffset);
      characterList = characterList.slice(startOffset);
    } else if (key === endKey) {
      text = text.slice(0, endOffset);
      characterList = characterList.slice(0, endOffset);
    }

    return block.merge({
      text,
      characterList,
    });
  });

  const newContentState = contentState.set('blockMap', modifiedBlocks);
  return newContentState;
};

/**
 * Returns ContentState containing only the given block (whole block).
 * Used in Safari when selection is collapsed but we want to copy the current block (e.g. block ends with variable).
 */
export function getContentStateForBlock(editorState: any, blockKey: string): any {
  const contentState = editorState.getCurrentContent();
  const block = contentState.getBlockForKey(blockKey);
  if (!block) return null;
  const singleBlockMap = contentState.getBlockMap().filter((_: any, key: string) => key === blockKey);
  return contentState.set('blockMap', singleBlockMap);
}

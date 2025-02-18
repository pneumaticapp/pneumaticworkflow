export const getSelectedContent = (editorState: any) => {
  const contentState = editorState.getCurrentContent();
  const selection = editorState.getSelection();

  if (selection.isCollapsed()) {
    return null;
  }

  const startKey = selection.getStartKey();
  const endKey = selection.getEndKey();
  const startOffset = selection.getStartOffset();
  const endOffset = selection.getEndOffset();

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

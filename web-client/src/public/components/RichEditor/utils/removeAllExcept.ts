import { EditorState, Modifier, SelectionState } from "draft-js";

export const removeAllExcept = (editorState: any, allowedStyles = new Set(), allowedBlockTypes = new Set()) => {
  let contentState = editorState.getCurrentContent();
  const entityMap = contentState.getEntityMap();
  const blockMap = contentState.getBlockMap();

  blockMap.forEach((block: any) => {
    block.findStyleRanges(
      (character: any) => character.getStyle().some((style: any) => !allowedStyles.has(style)),
      (start: any, end: any) => {
        const selection = SelectionState.createEmpty(block.getKey()).merge({
          anchorOffset: start,
          focusOffset: end,
        });

        const stylesToRemove = block.getInlineStyleAt(start).filter((style: any) => !allowedStyles.has(style));

        stylesToRemove.forEach((style: any) => {
          contentState = Modifier.removeInlineStyle(contentState, selection, style);
        });
      },
    );
  });

  blockMap.forEach((block: any) => {
    const key = block.getEntityAt(1);
    if (key) {
      const type = entityMap.get(key).getType();
      if (type === 'variable') return;
    }

    block.findEntityRanges(
      (character: any) => character.getEntity() !== null,
      (start: any, end: any) => {
        const selection = SelectionState.createEmpty(block.getKey()).merge({
          anchorOffset: start,
          focusOffset: end,
        });

        contentState = Modifier.applyEntity(contentState, selection, null);
      },
    );
  });

  blockMap.forEach((block: any) => {
    if (!allowedBlockTypes.has(block.getType())) {
      const selection = SelectionState.createEmpty(block.getKey());
      contentState = Modifier.setBlockType(contentState, selection, 'unstyled');
    }
  });

  return EditorState.push(editorState, contentState, 'change-block-type');
};

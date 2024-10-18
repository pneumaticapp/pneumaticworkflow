/* eslint-disable */
/* prettier-ignore */
import { RawDraftContentState, RawDraftContentBlock, RawDraftEntityRange } from 'draft-js';
import { flatten } from '../../../../utils/helpers';
import { ECustomEditorEntities } from '../types';

const atomicEntities = [
  ECustomEditorEntities.Image,
  ECustomEditorEntities.Video,
  ECustomEditorEntities.File,
];

export function normalizeDraftRaw(raw: RawDraftContentState): RawDraftContentState {
  const splitBlock = (block: RawDraftContentBlock) => {
    if (!block.entityRanges || !block.text) {
      return block;
    }

    const splittedBlocks = [];
    let currentBlock = {} as Omit<RawDraftContentBlock, 'key'>;
    let currentBlockIndex = 0;
    let state: 'char-added' | 'block-added' = 'block-added';

    for (let i = 0; i < block.text.length; i++ ) {
      if (state === 'block-added') {
        currentBlock = {
          depth: block.depth,
          type: block.type,
          data: block.data,
          entityRanges: [],
          inlineStyleRanges: [],
          text: '',
        };

        currentBlockIndex = 0;
      }

      if (block.text[i] === '\n') {
        state = 'block-added';
        splittedBlocks.push(currentBlock);

        continue;
      }

      currentBlock.text = currentBlock.text + block.text[i];

      const [currentEntityRange, currentEntityType] = getBlockEntityByOffset(raw, block, i);
      if (currentEntityRange) {
        currentBlock.entityRanges.push({ ...currentEntityRange, offset: currentBlockIndex});
      }
      const style = block.inlineStyleRanges.find(range => range.offset === i);
      if (style) {
        currentBlock.inlineStyleRanges.push({ ...style, offset: currentBlockIndex});
      }

      if (currentEntityType && atomicEntities.includes(currentEntityType)) {
        currentBlock.type = 'atomic';
        state = 'block-added';
        splittedBlocks.push(currentBlock);

        continue;
      }

      if (i === block.text.length - 1) {
        state = 'block-added';
        splittedBlocks.push(currentBlock);

        continue;
      }

      const [, nextCharEntityType] = getBlockEntityByOffset(raw, block, i + 1);
      if (nextCharEntityType && atomicEntities.includes(nextCharEntityType)) {
        state = 'block-added';
        splittedBlocks.push(currentBlock);

        continue;
      }

      currentBlockIndex++;
      state = 'char-added';
    }

    return splittedBlocks;
  };

  return {
    ...raw,
    blocks: flatten(raw.blocks.map(splitBlock)),
  } as RawDraftContentState;
}

function getBlockEntityByOffset(
  raw: RawDraftContentState,
  block: RawDraftContentBlock,
  offset: number,
): [RawDraftEntityRange | undefined, ECustomEditorEntities | undefined] {
  const entityRange = block.entityRanges.find(range => range.offset === offset);

  if (!entityRange) {
    return [undefined, undefined];
  }

  const entityType = entityRange && raw.entityMap[entityRange.key]?.type as ECustomEditorEntities;

  return [entityRange, entityType];
}

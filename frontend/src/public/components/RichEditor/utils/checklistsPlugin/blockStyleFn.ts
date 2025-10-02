
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';

import type { ContentBlock } from 'draft-js';

const blockStyleFn = (block: ContentBlock) => {
  if (block.getType() === CHECKABLE_LIST_ITEM) {
    return CHECKABLE_LIST_ITEM;
  }

  return undefined;
};

export default blockStyleFn;

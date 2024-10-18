import { ContentBlock } from 'draft-js';
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';

function createBlockRendererFn({ CheckableListItem }: any) {
  return (block: ContentBlock) => {
    if (block.getType() === CHECKABLE_LIST_ITEM) {
      return {
        component: CheckableListItem,
        props: {},
      };
    }

    return undefined;
  };
} 

export default createBlockRendererFn;

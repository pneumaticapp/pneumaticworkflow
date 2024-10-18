import {
  blockRenderMap,
  blockRenderMapForSameWrapperAsUnorderedListItem,
  // @ts-ignore
} from 'draft-js-checkable-list-item';

import type { Config } from '.';

const createBlockRenderMap = (config: Config) => {
  return config.sameWrapperAsUnorderedListItem ? blockRenderMapForSameWrapperAsUnorderedListItem : blockRenderMap;
};

export default createBlockRenderMap;

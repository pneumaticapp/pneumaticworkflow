import { ContentBlock, EditorState } from 'draft-js';
// @ts-ignore
import { mergeBlockDataByKey } from 'draft-js-modifiers';
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';

import { TChecklistItemData } from './types';

import { createUniqueId } from '../../../../utils/createId';

export function setChecklistApiNames(editorState: EditorState) {
  let resultEditorState = editorState;
  let currentListApiName = '';

  const contentState = editorState.getCurrentContent();
  const usedListsApiNames: string[] = [];
  const usedItemsApiNames: string[] = [];

  contentState.getBlockMap().forEach((block, key) => {
    if (!key || !block || block.getType() !== CHECKABLE_LIST_ITEM) {
      return;
    }

    if (!currentListApiName) {
      currentListApiName = getApiName(EApiNameType.Checklist, block, usedListsApiNames);
    }

    const itemApiName = getApiName(EApiNameType.ChecklistItem, block, usedItemsApiNames);
    usedItemsApiNames.push(itemApiName);

    resultEditorState = mergeBlockDataByKey(resultEditorState, key, {
      listApiName: currentListApiName,
      itemApiName,
    } as TChecklistItemData);

    const nextBlock = contentState.getBlockAfter(key);
    if (!nextBlock || nextBlock.getType() !== CHECKABLE_LIST_ITEM) {
      usedListsApiNames.push(currentListApiName);
      currentListApiName = '';
    }
  });

  return resultEditorState;
}

enum EApiNameType {
  Checklist = 'checklist',
  ChecklistItem = 'checklist-item',
}

const getApiName = (type: EApiNameType, block: ContentBlock, usedApiNames: string[]) => {
  const getSetApiNameMap = {
    [EApiNameType.Checklist]: () => block.getData().get('listApiName'),
    [EApiNameType.ChecklistItem]: () => block.getData().get('itemApiName'),
  };

  const createApiNameMap = {
    [EApiNameType.Checklist]: () => createUniqueId('clist-xxxyxx'),
    [EApiNameType.ChecklistItem]: () => createUniqueId('citem-xxxyxx'),
  };

  const setApiName = getSetApiNameMap[type]();
  const createApiName = createApiNameMap[type];

  if (!setApiName) {
    return createApiName();
  }

  return usedApiNames.includes(setApiName) ? createApiName() : setApiName;
};

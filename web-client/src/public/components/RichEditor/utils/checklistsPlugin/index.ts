import { ComponentType } from 'react';
import { EditorPlugin } from '@draft-js-plugins/editor';
// @ts-ignore
import { CheckableListItem } from './CheckableListItem';
import { decorateComponentWithProps } from '../../../../utils/decorateComponentWithProps';
import createBlockRendererFn from './createBlockRendererFn';
import createBlockRenderMap from './createBlockRenderMap';

import blockStyleFn from './blockStyleFn';
import { ChecklistButton } from './ChecklistButton';

export type Config = {
  sameWrapperAsUnorderedListItem?: boolean,
}

export type CheckableListPlugin = EditorPlugin & {
  ChecklistButton: ComponentType<{}>;
};

const checkableListPlugin = (config: Config = {}): CheckableListPlugin => {
  const store = {
    getEditorState: null,
    setEditorState: null,
  };

  const blockRendererConfig = {
    CheckableListItem,
    ...config,
  };

  const blockRenderMapConfig = {
    sameWrapperAsUnorderedListItem: !!config.sameWrapperAsUnorderedListItem,
  };

  const buttonConfig = { store };

  return {
    initialize({ setEditorState, getEditorState }: any) {
      store.setEditorState = setEditorState;
      store.getEditorState = getEditorState;
    },
    blockRendererFn: createBlockRendererFn(blockRendererConfig),
    blockRenderMap: createBlockRenderMap(blockRenderMapConfig),
    ChecklistButton: decorateComponentWithProps(ChecklistButton, buttonConfig),
    blockStyleFn,
  };
};

export default checkableListPlugin;

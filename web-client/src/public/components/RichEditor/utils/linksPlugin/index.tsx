/* eslint-disable */
/* prettier-ignore */
import React, {
  ComponentType,
  ReactElement,
} from 'react';
import { EditorPlugin, EditorRef } from '@draft-js-plugins/editor';
// tslint:disable-next-line: match-default-export-name
import EditorUtils, { createStore, Store } from '@draft-js-plugins/utils';
import { EditorState, SelectionState } from 'draft-js';
import { Link } from './components/Link';
import { LinkButton } from './components/LinkButton';
import { linkStrategy } from './linkStrategy';
import { AddLinkForm } from './components/AddLinkForm';

export interface IAnchorPluginConfig {}

export type AnchorPlugin = EditorPlugin & {
  LinkButton: ComponentType<{}>;
  AddLinkForm: ComponentType<{}>;
};

export interface IStoreItemMap {
  isVisible?: boolean;
  selection?: SelectionState;
  buttonRef?: React.RefObject<HTMLButtonElement>;
  getEditorRef?(): EditorRef;
  getEditorState?(): EditorState;
  setEditorState?(state: EditorState): void;
}

export type IAnchorPluginStore = Store<IStoreItemMap>;

// tslint:disable-next-line: no-default-export
export default (config: IAnchorPluginConfig = {}): AnchorPlugin => {
  const store: IAnchorPluginStore = createStore<IStoreItemMap>({
    isVisible: false,
    getEditorState: undefined,
    setEditorState: undefined,
  });

  const removeLinkAtSelection = () => {
    const setEditorState = store.getItem('setEditorState');
    const getEditorState = store.getItem('getEditorState');
    if (!setEditorState || !getEditorState) {
      return;
    }

    setEditorState?.(
      EditorUtils.removeLinkAtSelection(getEditorState?.()),
    );
  };

  const DecoratedLinkButton = (): ReactElement => (
    <LinkButton
      store={store}
      onRemoveLinkAtSelection={removeLinkAtSelection}
    />
  );

  const DecoratedAddLinkForm = () => {
    return (
      <AddLinkForm store={store} />
    );
  };

  return {
    initialize: ({ getEditorState, setEditorState, getEditorRef }) => {
      store.updateItem('getEditorState', getEditorState);
      store.updateItem('setEditorState', setEditorState);
      store.updateItem('getEditorRef', getEditorRef);
    },
    // Re-Render the AddLinkForm on selection change
    onChange: (editorState) => {
      const newSelection = editorState.getSelection();
      store.updateItem('selection', newSelection);

      return editorState;
    },
    decorators: [
      {
        strategy: linkStrategy,
        component: Link,
      },
    ],
    LinkButton: DecoratedLinkButton,
    AddLinkForm: DecoratedAddLinkForm,
  };
};

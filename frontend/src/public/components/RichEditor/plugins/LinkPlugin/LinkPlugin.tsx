import React, { useMemo, createContext, useContext } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

import { LinkUrlForm } from './LinkUrlForm';
import { useLinkFormState } from '../../hooks/useLinkFormState';
import { useLinkActions } from '../../hooks/useLinkActions';
import type { ILinkPluginContextValue, ILinkPluginProviderProps } from './types';

export const LinkPluginContext = createContext<ILinkPluginContextValue | null>(null);

export function useLinkPlugin(): ILinkPluginContextValue {
  const context = useContext(LinkPluginContext);

  if (context == null) {
    throw new Error('useLinkPlugin must be used within LinkPluginProvider');
  }

  return context;
}

export function LinkPluginProvider({ children, editorContainerRef }: ILinkPluginProviderProps): React.ReactElement {
  const [editor] = useLexicalComposerContext();
  const { formState, openLinkForm, closeLinkForm } = useLinkFormState();
  const { applyLink } = useLinkActions(editor, closeLinkForm);

  const contextValue = useMemo<ILinkPluginContextValue>(
    () => ({
      openLinkForm,
      closeLinkForm,
      applyLink,
    }),
    [openLinkForm, closeLinkForm, applyLink],
  );

  return (
    <LinkPluginContext.Provider value={contextValue}>
      {children}
      <LinkUrlForm
        anchorElement={formState.anchorElement}
        anchorRect={formState.anchorRect}
        editorContainerRef={editorContainerRef}
        getAnchorRect={formState.getAnchorRect}
        formMode={formState.formMode}
        isVisible={formState.isOpen}
        onClose={closeLinkForm}
        onSubmit={applyLink}
      />
    </LinkPluginContext.Provider>
  );
}

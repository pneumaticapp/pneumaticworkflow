import React, { useMemo, createContext, useContext } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';

import { LinkUrlForm } from './LinkUrlForm';
import { useLinkFormState, useLinkActions } from '../../LexicalRichEditor/hooks';
import type { ILinkPluginContextValue } from './types';



export const LinkPluginContext = createContext<ILinkPluginContextValue | null>(null);

export function useLinkPlugin(): ILinkPluginContextValue {
  const context = useContext(LinkPluginContext);

  if (context == null) {
    throw new Error('useLinkPlugin must be used within LinkPluginProvider');
  }

  return context;
}

interface ILinkPluginProviderProps {
  children: React.ReactNode;
  editorContainerRef?: React.RefObject<HTMLDivElement | null>;
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

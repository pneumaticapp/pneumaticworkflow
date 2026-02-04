import * as React from 'react';
import { Desktop, Mobile } from '../media';
import {
  BoldButton,
  ItalicButton,
  OrderedListButton,
  UnorderedListButton,
  ImageAttachmentButton,
  VideoAttachmentButton,
  FileAttachmentButton,
  Separator,
} from './toolbarSettings';
import { IExtendedToolbarChildrenProps } from './toolbarSettings/utils/types';

type TAttachmentButtonProps = IExtendedToolbarChildrenProps & {
  uploadAttachments: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
};

export interface IEditorToolbarProps {
  Toolbar: React.ComponentType<{ children: (props: IExtendedToolbarChildrenProps) => React.ReactNode }>;
  LinkButton: React.ComponentType<IExtendedToolbarChildrenProps>;
  /** Injected by plugin with store; no toolbar props passed from here */
  ChecklistButton: React.ComponentType<Record<string, never>>;
  isModal?: boolean;
  withChecklists: boolean;
  uploadAttachments: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
}

export function EditorToolbar({
  Toolbar,
  LinkButton,
  ChecklistButton,
  isModal,
  withChecklists,
  uploadAttachments,
}: IEditorToolbarProps) {
  return (
    <>
      <Desktop>
        <Toolbar>
          {(externalProps: IExtendedToolbarChildrenProps) => {
            const themeWithModal = { ...externalProps.theme, isModal };
            const propsWithTheme: IExtendedToolbarChildrenProps = { ...externalProps, theme: themeWithModal };
            const attachmentProps: TAttachmentButtonProps = { ...propsWithTheme, uploadAttachments };
            return (
              <>
                <BoldButton {...propsWithTheme} />
                <ItalicButton {...propsWithTheme} />
                <OrderedListButton {...propsWithTheme} />
                <UnorderedListButton {...propsWithTheme} />
                <LinkButton {...externalProps} />
                {withChecklists && <ChecklistButton />}
                <Separator />
                <ImageAttachmentButton {...attachmentProps} />
                <VideoAttachmentButton {...attachmentProps} />
                <FileAttachmentButton {...attachmentProps} />
              </>
            );
          }}
        </Toolbar>
      </Desktop>
      <Mobile>
        <Toolbar>
          {(externalProps: IExtendedToolbarChildrenProps) => {
            const themeWithModal = { ...externalProps.theme, isModal };
            const attachmentProps: TAttachmentButtonProps = { ...externalProps, theme: themeWithModal, uploadAttachments };
            return <FileAttachmentButton {...attachmentProps} />;
          }}
        </Toolbar>
      </Mobile>
    </>
  );
}

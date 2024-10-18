/* eslint-disable */
/* prettier-ignore */
import { ComponentType } from 'react';
import { EditorPlugin } from '@draft-js-plugins/editor';
import { addAttachment } from './modifiers/addAttachment';
import { ContentBlock, ContentState } from 'draft-js';
import { ECustomEditorEntities } from '../types';

export interface IAttachmentProps {
  block: ContentBlock;
  className?: string;
  contentState: ContentState;
  deleteAttachment(block: ContentBlock): void;
}

export interface IAttachmentPluginConfig {
  decorator?(component: ComponentType<IAttachmentProps>): ComponentType<IAttachmentProps>;
  imageComponent: ComponentType<IAttachmentProps>;
  fileComponent: ComponentType<IAttachmentProps>;
  videoComponent: ComponentType<IAttachmentProps>;
}

export type ImageEditorPlugin = EditorPlugin & {
  addAttachment: typeof addAttachment;
};

// tslint:disable-next-line: no-default-export
export default (config: IAttachmentPluginConfig): ImageEditorPlugin => {
  const { decorator, imageComponent, fileComponent, videoComponent } = config;
  const Image = decorator ? decorator(imageComponent) : imageComponent;
  const File = decorator ? decorator(fileComponent) : fileComponent;
  const Video = decorator ? decorator(videoComponent) : videoComponent;

  return {
    blockRendererFn: (block, { getEditorState }) => {
      if (block.getType() === 'atomic') {
        const contentState = getEditorState().getCurrentContent();
        const entity = block.getEntityAt(0);
        if (!entity) {
          return null;
        }

        const type = contentState.getEntity(entity).getType() as ECustomEditorEntities;
        type TRenderMapItem = {
          [key in ECustomEditorEntities]?: {
            component: ComponentType<IAttachmentProps>;
            editable: boolean;
          };
        };
        const renderMap: TRenderMapItem = {
          [ECustomEditorEntities.Image]: {
            component: Image,
            editable: false,
          },
          [ECustomEditorEntities.Video]: {
            component: Video,
            editable: false,
          },
          [ECustomEditorEntities.File]: {
            component: File,
            editable: false,
          },
        };

        return renderMap[type] || null;
      }

      return null;
    },
    addAttachment,
  };
};

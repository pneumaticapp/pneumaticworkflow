/* eslint-disable */
/* prettier-ignore */
/* eslint-disable */
import React, { MouseEvent, ReactNode } from 'react';
import classnames from 'classnames';
import { RichUtils } from 'draft-js';

import { IExtendedToolbarChildrenProps } from './types';
import { CustomTooltip } from '../../../UI';

interface ICreateBlockStyleButtonProps {
  blockType: string;
  tooltipText: string;
  children: ReactNode;
}

export function createBlockStyleButton({ blockType, tooltipText, children }: ICreateBlockStyleButtonProps) {
  return function BlockStyleButton(props: React.PropsWithChildren<IExtendedToolbarChildrenProps>) {
    const buttonRef = React.useRef<HTMLButtonElement>(null);

    const toggleStyle = (event: MouseEvent): void => {
      event.preventDefault();
      props.setEditorState(RichUtils.toggleBlockType(props.getEditorState(), blockType));
    };

    const preventBubblingUp = (event: MouseEvent): void => {
      event.preventDefault();
    };

    const blockTypeIsActive = (): boolean => {
      // if the button is rendered before the editor
      if (!props.getEditorState) {
        return false;
      }

      const editorState = props.getEditorState();
      const type = editorState.getCurrentContent().getBlockForKey(editorState.getSelection().getStartKey()).getType();

      return type === blockType;
    };

    const { theme } = props;
    const className = blockTypeIsActive() ? classnames(theme.button, theme.active) : theme.button;

    return (
      <div className={theme.buttonWrapper} onMouseDown={preventBubblingUp}>
        <CustomTooltip target={buttonRef} tooltipText={tooltipText} isModal={theme.isModal} />
        <button ref={buttonRef} children={children} className={className} onClick={toggleStyle} type="button" />
      </div>
    );
  };
}

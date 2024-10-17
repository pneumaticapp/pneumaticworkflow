/* eslint-disable */
/* prettier-ignore */
import React, { MouseEvent, ReactNode } from 'react';
import * as classnames from 'classnames';
import { ContentState, EditorState, RichUtils, SelectionState } from 'draft-js';
// tslint:disable-next-line: no-implicit-dependencies
import { ToolbarChildrenProps } from '@draft-js-plugins/static-toolbar/lib/components/Toolbar';
import { extractLinks } from '@draft-js-plugins/linkify';

import { getEntitiesByLogic } from '../../utils/getEntitiesByLogic';
import { ECustomEditorEntities } from '../../utils/types';
import { CustomTooltip } from '../../../UI';

interface ICreateInlineStyleButtonProp {
  style: string;
  tooltipText: string;
  children: ReactNode;
}

export function createInlineStyleButton({
  style,
  tooltipText,
  children,
}: ICreateInlineStyleButtonProp) {
  return function InlineStyleButton(props: React.PropsWithChildren<ToolbarChildrenProps>) {
    const buttonRef = React.useRef<HTMLButtonElement>(null);

    const toggleStyle = (event: MouseEvent): void => {
      event.preventDefault();
      event.stopPropagation();

      const editorState = props.getEditorState();
      const newSelection = getInlineStyleModificationSelection(editorState);

      if (newSelection.isCollapsed()) {
        props.setEditorState(
          RichUtils.toggleInlineStyle(props.getEditorState(), style),
        );

        return;
      }

      const newEditorState = RichUtils.toggleInlineStyle(
        EditorState.forceSelection(editorState, newSelection),
        style,
      );
      props.setEditorState(newEditorState);
    };

    const preventBubblingUp = (event: MouseEvent): void => {
      event.preventDefault();
    };

    // we check if this.props.getEditorstate is undefined first in case the button is rendered before the editor
    const styleIsActive = (): boolean =>
      props.getEditorState &&
      props.getEditorState().getCurrentInlineStyle().has(style);

    const { theme } = props;
    const className = styleIsActive()
      ? classnames(theme.button, theme.active)
      : theme.button;

    return (
      <div className={theme.buttonWrapper} onMouseDown={preventBubblingUp}>
        <CustomTooltip target={buttonRef} tooltipText={tooltipText} />
        <button
          ref={buttonRef}
          className={className}
          onClick={toggleStyle}
          type="button"
          children={children}
        />
      </div>
    );
  };
}

export const getInlineStyleModificationSelection = (editorState: EditorState) => {
  const currentContent = editorState.getCurrentContent();
  const selectionState = editorState.getSelection();
  const startBlockKey = selectionState.getStartKey();
  const endBlockKey = selectionState.getEndKey();

  let selectionStartIndex = selectionState.getStartOffset();
  let selectionEndIndex = selectionState.getEndOffset();

  const startBlockEntitiesRanges = getBlockEntitiesRanges(currentContent, startBlockKey);
  startBlockEntitiesRanges.forEach((entityRanges) => {
    if (selectionStartIndex > entityRanges.startIndex && selectionStartIndex < entityRanges.endIndex) {
      selectionStartIndex = entityRanges.startIndex;
    }
  });

  const endBlockEntitiesRanges = getBlockEntitiesRanges(currentContent, endBlockKey);
  endBlockEntitiesRanges.forEach((entityRanges) => {
    if (selectionEndIndex > entityRanges.startIndex && selectionEndIndex < entityRanges.endIndex) {
      selectionEndIndex = entityRanges.endIndex;
    }
  });

  const newSelection = new SelectionState({
    anchorKey: startBlockKey,
    anchorOffset: selectionStartIndex,
    focusKey: endBlockKey,
    focusOffset: selectionEndIndex,
  });

  return newSelection;
};

const getBlockEntitiesRanges = (contentState: ContentState, blockKey: string) => {
  const block = contentState.getBlockForKey(blockKey);
  const blockText = block.getText();

  const blockLinks = (extractLinks(blockText) || []) as { index: number; lastIndex: number }[];
  const linksWithNames = getEntitiesByLogic(
    contentState,
    entity => entity.getType() === ECustomEditorEntities.Link,
    blockKey,
  );
  const blockMentions = getEntitiesByLogic(
    contentState,
    entity => entity.getType() === ECustomEditorEntities.Mention,
    blockKey,
  );
  const blockVariables = getEntitiesByLogic(
    contentState,
    entity => entity.getType() === ECustomEditorEntities.Variable,
    blockKey,
  );

  const sortedEntitiesRanges = [
    ...blockLinks,
    ...linksWithNames,
    ...blockMentions,
    ...blockVariables,
  ]
    .sort((a, b) => a.index - b.index)
    .map(({ index, lastIndex }) => ({ startIndex: index, endIndex: lastIndex }));

  return sortedEntitiesRanges;
};

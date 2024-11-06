/* eslint-disable */
/* prettier-ignore */
import React, { MouseEvent, ReactElement, useEffect } from 'react';
import { useIntl } from 'react-intl';
// tslint:disable-next-line: match-default-export-name
import EditorUtils from '@draft-js-plugins/utils';
import { IAnchorPluginStore } from '..';
import { LinkButtonIcon } from '../../../../icons';
import { CustomTooltip } from '../../../../UI';

import theme from '../../../toolbarSettings/ButtonStyles.css';

export interface ILinkButtonParams {
  store: IAnchorPluginStore;
  onRemoveLinkAtSelection(): void;
}

export const LinkButton = ({
  onRemoveLinkAtSelection,
  store,
}: ILinkButtonParams): ReactElement => {
  const { formatMessage } = useIntl();

  const buttonRef = React.useRef<HTMLButtonElement>(null);

  useEffect(() => {
    store.updateItem('buttonRef', buttonRef);
  }, []);

  const onAddLinkClick = (event: MouseEvent): void => {
    event.preventDefault();
    event.stopPropagation();

    store.updateItem('isVisible', true);
  };

  const editorState = store.getItem('getEditorState')?.();
  const hasLinkSelected = editorState
    ? EditorUtils.hasEntity(editorState, 'LINK')
    : false;

  const preventBubblingUp = (event: MouseEvent): void => {
    event.preventDefault();
  };

  return (
    <div className={theme.buttonWrapper} onMouseDown={preventBubblingUp}>
      <CustomTooltip target={buttonRef} tooltipText={formatMessage({ id: 'editor.add-link' })} />
      <button
        ref={buttonRef}
        className={theme.button}
        onClick={hasLinkSelected ? onRemoveLinkAtSelection : onAddLinkClick}
        type="button"
      >
        <LinkButtonIcon />
      </button>
    </div>
  );
};

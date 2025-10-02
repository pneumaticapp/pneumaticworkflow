/* eslint-disable jsx-a11y/control-has-associated-label */
/* eslint-disable jsx-a11y/no-static-element-interactions */
import React, { MouseEventHandler } from 'react'
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { RichUtils, EditorState } from 'draft-js';
// @ts-ignore
import { CHECKABLE_LIST_ITEM } from 'draft-js-checkable-list-item';
import { ChecklistIcon } from '../../../../icons';
import { Tooltip } from '../../../../UI';
// import { ELearnMoreLinks } from '../../../../../constants/defaultValues';

import theme from '../../../toolbarSettings/ButtonStyles.css';

export type TChecklistButtonProps = {
  store: {
    setEditorState: (editorState: EditorState) => void;
    getEditorState: () => EditorState;
  };
}

export const ChecklistButton: React.FC<TChecklistButtonProps> = props => {
  const { formatMessage } = useIntl();

  const toggleType = (event: React.SyntheticEvent<HTMLButtonElement>): void => {
    event.preventDefault()
    const { store } = props;

    store.setEditorState(
      RichUtils.toggleBlockType(
        store.getEditorState(),
        CHECKABLE_LIST_ITEM
      )
    )
  }

  const isActive = () => {
    const { store: { getEditorState } } = props;

    return RichUtils.getCurrentBlockType(getEditorState()) === CHECKABLE_LIST_ITEM
  }

  const preventBubblingUp: MouseEventHandler = event => {
    event.preventDefault();
  };

  return (
    <Tooltip content={(
      <>
        {formatMessage({ id: 'editor.add-checklist-item' })}

        {/* <div>
          <a target="_blank" rel="noreferrer" href={ELearnMoreLinks.Checklists}>
            {formatMessage({ id: 'dashboard.integrations-tooltip-link' })}
          </a>
        </div> */}
      </>
    )}>
      <div className={theme.buttonWrapper} onMouseDown={preventBubblingUp}>
        <button
          className={classnames(theme.button, isActive() && theme.active)}
          onClick={toggleType}
          type="button"
        >
          <ChecklistIcon />
        </button>
      </div>
    </Tooltip >
  );
}

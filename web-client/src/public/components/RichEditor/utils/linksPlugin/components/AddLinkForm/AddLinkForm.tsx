/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count

import React, {
  useState,
  useEffect,
  useRef,
  CSSProperties,
} from 'react';
import { usePopper } from 'react-popper';
// tslint:disable-next-line: match-default-export-name
import EditorUtils from '@draft-js-plugins/utils';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';
import { EditorState, getVisibleSelectionRect } from 'draft-js';

import URLUtils from '../../utils/URLUtils';
import { IAnchorPluginStore } from '../..';
import { InputField } from '../../../../../UI';
import { addNewLinkEntity } from '../../utils/addNewLink';
import { SquaredCheckButtonIcon, SquaredCrossButtonIcon } from '../../../../../icons';

import styles from './AddLinkForm.css';

type TAddLinkFormMode =
  | 'create-link-at-selection'
  | 'create-link-from-scratch';

interface IAddLinkFormParams {
  store: IAnchorPluginStore;
}

export const AddLinkForm = (props: IAddLinkFormParams) => {
  // used only if link is creating for selected text
  const [formPosition, setFormPosition] = useState<{
    top: number;
    left: number;
  } | undefined>();

  const formRef = useRef<HTMLDivElement>(null);
  const linkUrlFieldRef = useRef<HTMLInputElement>(null);
  const linkTextFieldRef = useRef<HTMLInputElement>(null);

  const { formatMessage } = useIntl();
  const [editingLinkUrl, setEditingLinkUrl] = useState('');
  const [editingLinkText, setEditingLinkText] = useState('');
  const [linkUrlError, setLinkUrlError] = useState('');
  const [linkTextError, setLinkTextError] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [formMode, setFormMode] = useState<TAddLinkFormMode | null>();
  const linkButtonRef = props.store.getItem('buttonRef');

  useEffect(() => {
    const handleClose = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleClose);

    return () => window.removeEventListener('keydown', handleClose);
  }, []);

  const {
    styles: popperStyles,
    attributes,
  } = usePopper(linkButtonRef?.current, formRef.current, {
    placement: 'top',
    modifiers: [{
      name: 'offset',
      options: {
        offset: [0, 10],
      },
    }],
  });

  const onClose = () => {
    setEditingLinkUrl('');
    setEditingLinkText('');
    setLinkUrlError('');
    setLinkTextError('');
    setIsVisible(false);
  };

  useEffect(() => {
    if (isVisible) {
      const selection = props.store.getItem('selection');
      const editorState = props.store.getItem('getEditorState')?.();
      const setEditorState = props.store.getItem('setEditorState');

      if (!selection?.getHasFocus()) {
        setEditorState!(EditorState.moveFocusToEnd(editorState!));
      }

      const newMode: TAddLinkFormMode = selection?.isCollapsed() ? 'create-link-from-scratch' : 'create-link-at-selection';
      setFormMode(newMode);
    } else {
      setFormMode(null);
    }
  }, [isVisible]);

  useEffect(() => {
    const focusFieldMap = {
      'create-link-from-scratch': linkTextFieldRef,
      'create-link-at-selection': linkUrlFieldRef,
    };

    setTimeout(() => {
      if (formMode) {
        focusFieldMap[formMode].current?.focus();
      }
    });
  }, [isVisible, formMode]);

  useEffect(() => {
    const recalculateFormPositionBySelection = () => {
      // need to wait a tick for window.getSelection() to be accurate
      // when focusing editor with already present selection
      setTimeout(() => {
        // The editor root should be two levels above the node from
        // `getEditorRef`. In case this changes in the future, we
        // attempt to find the node dynamically by traversing upwards.
        const editorRef = props.store.getItem('getEditorRef')!();
        if (!editorRef) {
          return;
        }

        // This keeps backwards compatibility with React 15
        let editorRoot =
          editorRef.refs && editorRef.refs.editor
            ? editorRef.refs.editor
            : editorRef.editor;
        while (editorRoot.className.indexOf('DraftEditor-root') === -1) {
          editorRoot = editorRoot.parentNode as HTMLElement;
        }
        const editorRootRect = editorRoot.getBoundingClientRect();

        const parentWindow =
          editorRoot.ownerDocument && editorRoot.ownerDocument.defaultView;
        const selectionRect = getVisibleSelectionRect(parentWindow || window);
        if (!selectionRect) {
          return;
        }

        const extraTopOffset = 0;

        // Account for scrollTop of all ancestors
        let scrollOffset = 0;
        let ancestorNode = editorRoot.parentNode as HTMLElement;
        while (ancestorNode !== null
          && ancestorNode.nodeName !== 'HTML'
          && !ancestorNode.classList.contains('modal') // in case form is inside a modal
        ) {
          scrollOffset += ancestorNode.scrollTop ?? 0;
          ancestorNode = ancestorNode.parentNode as HTMLElement;
        }

        const position = {
          top:
            editorRoot.offsetTop -
            scrollOffset -
            formRef.current!.offsetHeight +
            (selectionRect.top - editorRootRect.top) +
            extraTopOffset,
          left:
            editorRoot.offsetLeft +
            (selectionRect.left - editorRootRect.left) +
            selectionRect.width / 2,
        };

        setFormPosition(position);
      });
    };

    recalculateFormPositionBySelection();
  }, [isVisible]);

  useEffect(() => {
    const updateIsVisibleState = () => {
      setIsVisible(props.store.getItem('isVisible') || false);
    };

    props.store.subscribeToItem('isVisible', updateIsVisibleState);

    return () => props.store.unsubscribeFromItem('isVisible', updateIsVisibleState);
  }, []);

  const getContainerStyleAttibutes = () => {
    // If a link is creating from scratch — not for selected text – we delegate
    // calculating form position to pooper.js, and render form behind the
    // Add Link button in the editor toolbar
    if (formMode === 'create-link-from-scratch') {
      return { style: popperStyles.popper, ...attributes.popper };
    }

    const style: CSSProperties = { ...formPosition! };

    if (isVisible) {
      style.visibility = 'visible';
      style.transform = 'translate(-50%) scale(1)';
      style.transition = 'transform 0.15s cubic-bezier(.3,1.2,.2,1)';
    } else {
      style.transform = 'translate(-50%) scale(0)';
      style.visibility = 'hidden';
    }

    return { style };
  };

  const isUrl = (urlValue: string): boolean => URLUtils.isUrl(urlValue);

  const submit = (): void => {
    if (!formMode) {
      return;
    }

    const setEditorState = props.store.getItem('setEditorState');
    const getEditorState = props.store.getItem('getEditorState');
    if (!setEditorState || !getEditorState) {
      return;
    }

    const url = URLUtils.normalizeUrl(editingLinkUrl);
    if (!isUrl(url)) {
      setLinkUrlError(formatMessage({ id: 'editor.link-url-invalid' }));

      return;
    }

    if (formMode === 'create-link-from-scratch' && !editingLinkText) {
      setLinkTextError(formatMessage({ id: 'editor.link-name-invalid' }));

      return;
    }

    const addLinkMap: { [key in TAddLinkFormMode]: (() => void) } = {
      'create-link-from-scratch': () => setEditorState(addNewLinkEntity(getEditorState(), editingLinkText, url)),
      'create-link-at-selection': () => setEditorState(EditorUtils.createLinkAtSelection(getEditorState(), url)),
    };
    addLinkMap[formMode]();
    onClose();
    setEditingLinkUrl('');
    setEditingLinkText('');
  };

  const onChangeUrlField: React.DOMAttributes<HTMLInputElement>['onChange'] = (event) => {
    setLinkUrlError('');
    setEditingLinkUrl(event.currentTarget.value);
  };

  const onChangeTextField: React.DOMAttributes<HTMLInputElement>['onChange'] = (event) => {
    setLinkTextError('');
    setEditingLinkText(event.currentTarget.value);
  };

  const renderForm = () => {
    if (!formMode) {
      return null;
    }

    const onKeyPress: React.DOMAttributes<HTMLInputElement>['onKeyPress'] = (event) => {
      if (event.key === 'Enter') {
        // prevent submitting in case RichEditor is inside a form
        event.preventDefault();

        submit();
      }
    };

    const linkTextField = (
      <InputField
        onKeyPress={onKeyPress}
        inputRef={linkTextFieldRef}
        value={editingLinkText}
        onChange={onChangeTextField}
        placeholder={formatMessage({ id: 'editor.link-text-placeholder' })}
        fieldSize="sm"
        className={styles['input-field']}
        errorMessage={linkTextError}
      />
    );
    const linkUrlField = (
      <div className={styles['url-field-wrapper']}>
        <InputField
          onKeyPress={onKeyPress}
          inputRef={linkUrlFieldRef}
          value={editingLinkUrl}
          onChange={onChangeUrlField}
          placeholder={formatMessage({ id: 'editor.link-url-placeholder' })}
          fieldSize="sm"
          className={classnames(styles['input-field'], styles['url-field'])}
          errorMessage={linkUrlError}
        />
        <div className={styles['controls']}>
          <button
            type="button"
            onClick={submit}
            className={styles['controls_button']}
          >
            <SquaredCheckButtonIcon />
          </button>

          <button
            type="button"
            className={styles['controls_button']}
            onClick={onClose}
          >
            <SquaredCrossButtonIcon />
          </button>
        </div>
      </div>
    );
    const formRenderMap: { [key in TAddLinkFormMode]: React.ReactNode } = {
      'create-link-from-scratch': (
        <>
          {linkTextField}
          <div className={styles['separator']} />
          {linkUrlField}
        </>
      ),
      'create-link-at-selection': (
        <>
          {linkUrlField}
        </>
      ),
    };

    return (
      <>
        {formRenderMap[formMode]}
      </>
    );
  };

  return (
    <OutsideClickHandler onOutsideClick={onClose} >
      <div
        ref={formRef}
        className={styles['container']}
        {...getContainerStyleAttibutes()}
      >
        {renderForm()}
      </div>
    </OutsideClickHandler>
  );
};

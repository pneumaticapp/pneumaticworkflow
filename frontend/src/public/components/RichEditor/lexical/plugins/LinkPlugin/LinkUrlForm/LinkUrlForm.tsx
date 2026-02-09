import React, { useRef, useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';

import URLUtils from '../../../../utils/linksPlugin/utils/URLUtils';
import { InputField } from '../../../../../UI';
import { SquaredCheckButtonIcon, SquaredCrossButtonIcon } from '../../../../../icons';
import { useFloatingFormPosition } from '../../../LexicalRichEditor/hooks';
import type { TLinkFormMode } from '../types';

import styles from './LinkUrlForm.css';



const FORM_OFFSET_PX = 8;

export interface ILinkUrlFormProps {
  anchorElement?: HTMLElement | null;
  anchorRect?: DOMRect | null;
  editorContainerRef?: React.RefObject<HTMLDivElement | null>;
  getAnchorRect?: (() => DOMRect | null) | null;
  formMode: TLinkFormMode;
  isVisible: boolean;
  onClose: () => void;
  onSubmit: (url: string, linkText?: string) => void;
}

export function LinkUrlForm({
  anchorElement,
  editorContainerRef,
  getAnchorRect,
  formMode,
  isVisible,
  onClose,
  onSubmit,
}: ILinkUrlFormProps): React.ReactElement | null {
  const formRef = useRef<HTMLDivElement>(null);
  const urlInputRef = useRef<HTMLInputElement>(null);
  const textInputRef = useRef<HTMLInputElement>(null);
  const ignoreOutsideClickUntilRef = useRef(0);
  const [url, setUrl] = useState('');
  const [linkText, setLinkText] = useState('');
  const [urlError, setUrlError] = useState('');
  const [linkTextError, setLinkTextError] = useState('');
  const { formatMessage } = useIntl();

  const { position, positionMode } = useFloatingFormPosition(formRef, {
    anchorElement,
    containerRef: editorContainerRef,
    getAnchorRect,
    isVisible,
    offsetPx: FORM_OFFSET_PX,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (isVisible) {
      ignoreOutsideClickUntilRef.current = Date.now() + 250;
      setUrl('');
      setLinkText('');
      setUrlError('');
      setLinkTextError('');
      const focusRef = formMode === 'create-link-from-scratch' ? textInputRef : urlInputRef;
      setTimeout(() => focusRef.current?.focus(), 0);
    }
  }, [isVisible, formMode]);

  const handleSubmit = useCallback(() => {
    const normalized = URLUtils.normalizeUrl(url);

    if (!URLUtils.isUrl(normalized)) {
      setUrlError(formatMessage({ id: 'editor.link-url-invalid' }));
      return;
    }

    if (formMode === 'create-link-from-scratch' && !linkText.trim()) {
      setLinkTextError(formatMessage({ id: 'editor.link-name-invalid' }));
      return;
    }
    
    onSubmit(normalized, formMode === 'create-link-from-scratch' ? linkText.trim() : undefined);
    onClose();
  }, [url, linkText, formMode, onSubmit, onClose, formatMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const handleOutsideClick = useCallback(() => {
    if (Date.now() < ignoreOutsideClickUntilRef.current) return;
    onClose();
  }, [onClose]);



  if (!isVisible) {
    return null;
  }

  const formJSX = (
    <OutsideClickHandler onOutsideClick={handleOutsideClick}>
      <div ref={formRef} className={styles['add-url-form']} style={{
        position: positionMode,
        zIndex: 2,
        transform: 'translateX(-50%)',
        left: position ? position.left : 0,
        top: position ? position.top : -9999,
        visibility: position ? 'visible' : 'hidden',
      }}>
        {formMode === 'create-link-from-scratch' && (
          <>
            <InputField
              inputRef={textInputRef}
              value={linkText}
              onChange={(e) => {
                setLinkTextError('');
                setLinkText(e.currentTarget.value);
              }}
              onKeyDown={handleKeyDown}
              placeholder={formatMessage({ id: 'editor.link-text-placeholder' })}
              fieldSize="sm"
              className={styles['add-url-form__input']}
              errorMessage={linkTextError}
            />
            <div className={styles['add-url-form__separator']} />
          </>
        )}
        <div className={styles['add-url-form__url-field-wrapper']}>
          <InputField
            inputRef={urlInputRef}
            value={url}
            onChange={(e) => {
              setUrlError('');
              setUrl(e.currentTarget.value);
            }}
            onKeyDown={handleKeyDown}
            placeholder={formatMessage({ id: 'editor.link-url-placeholder' })}
            fieldSize="sm"
            className={classnames(styles['add-url-form__input'], styles['add-url-form__input-url'])}
            errorMessage={urlError}
          />
          <div className={styles['add-url-form__actions']}>
            <button 
              type="button" 
              onClick={onClose} 
              className={styles['add-url-form__button']} 
              aria-label="Close"
            >
              <SquaredCrossButtonIcon />
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className={styles['add-url-form__button']}
              aria-label={formatMessage({ id: 'editor.add-link' })}
            >
              <SquaredCheckButtonIcon />
            </button>
          </div>
        </div>
      </div>
    </OutsideClickHandler>
  );

  const portalTarget = editorContainerRef?.current ?? document.body;
  return createPortal(formJSX, portalTarget);
}

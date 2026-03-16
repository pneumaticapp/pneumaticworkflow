import React, { memo, useCallback, useRef } from 'react';
import { CustomTooltip } from '../../../UI';
import type { IAttachmentToolbarButtonProps } from './types';

import styles from './EditorToolbar.css';

const AttachmentToolbarButton = memo(function AttachmentToolbarButton({
  tooltipText,
  ariaLabel,
  accept,
  multiple = true,
  isModal,
  onFileChange,
  children,
}: IAttachmentToolbarButtonProps): React.ReactElement {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleButtonMouseDown = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    inputRef.current?.click();
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFileChange(e);
      if (inputRef.current?.value) {
        inputRef.current.value = '';
      }
    },
    [onFileChange],
  );

  return (
    <div className={styles['button-wrapper']}>
      <CustomTooltip
        target={buttonRef}
        tooltipText={tooltipText}
        isModal={isModal}
      />
      <button
        ref={buttonRef}
        type="button"
        className={styles['button']}
        onMouseDown={handleButtonMouseDown}
        aria-label={ariaLabel}
      >
        {children}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className={styles['file-input']}
        onChange={handleInputChange}
      />
    </div>
  );
});

export { AttachmentToolbarButton };

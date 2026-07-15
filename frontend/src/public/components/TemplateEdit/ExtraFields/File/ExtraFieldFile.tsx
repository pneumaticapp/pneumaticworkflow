import React, { ChangeEvent, MouseEvent, useCallback, useEffect, useRef, useState } from 'react';
import classnames from 'classnames';
import AutosizeInput from 'react-input-autosize';
import { useIntl } from 'react-intl';

import { EExtraFieldMode } from '../../../../types/template';
import { logger } from '../../../../utils/logger';
import { parseMarkdownToFiles } from '../../../../utils/parseMarkdownFiles';
import { TUploadedFile, uploadFiles } from '../../../../utils/uploadFiles';
import { validateKickoffFieldName } from '../../../../utils/validators';
import { PencilSmallIcon } from '../../../icons';
import { IntlMessages } from '../../../IntlMessages';
import { Button } from '../../../UI/Buttons/Button';
import { NotificationManager } from '../../../UI/Notifications';
import kickoffStyles from '../../KickoffRedux/KickoffRedux.css';
import { IWorkflowExtraFieldProps } from '..';
import { ExtraFieldFilesGrid } from './ExtraFieldFilesGrid';
import styles from './ExtraFieldFile.css';

export function ExtraFieldFile({
  field,
  field: { name, isRequired },
  intl,
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
}: IWorkflowExtraFieldProps) {
  const [isUploading, setUploadingState] = useState(false);
  const initialFiles = field.attachments?.length
    ? field.attachments
    : parseMarkdownToFiles(field.markdownValue);
  const [filesToUpload, setFilesToUploadState] = useState<TUploadedFile[]>(initialFiles);
  const fieldNameInputRef = useRef<HTMLInputElement | null>(null);
  const uploadFieldRef = useRef<HTMLInputElement>(null);
  const [isFocused, setIsFocused] = useState(false);
  const { formatMessage } = useIntl();

  useEffect(() => {
    const nextFiles = field.attachments?.length
      ? field.attachments
      : parseMarkdownToFiles(field.markdownValue);

    setFilesToUploadState(nextFiles);
  }, [field.apiName, field.attachments, field.markdownValue]);

  useEffect(() => {
    const { current } = uploadFieldRef;

    if (current && current.value) {
      current.value = '';
    }
  }, [filesToUpload]);

  const handleChangeName = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      editField({ name: event.target.value });
    },
    [editField],
  );
  const handleUploadFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const { files } = event.target;

    if (!files) {
      return;
    }

    try {
      setUploadingState(true);
      const uploadedFiles = await uploadFiles(files);
      const successFiles = uploadedFiles.filter((file) => !file.error);
      const newUploadedFiles = [...filesToUpload, ...(successFiles as TUploadedFile[])];
      const newUploadedFilesIds = newUploadedFiles
        .filter((file) => !file.isRemoved)
        .map((file) => `[${file.name}](${file.url})`);

      setFilesToUploadState(newUploadedFiles);
      editField({ value: newUploadedFilesIds, attachments: newUploadedFiles });
    } catch (error) {
      NotificationManager.warning({ message: 'workflows.tasks-failed-to-upload-files' });
      logger.error(error);
    } finally {
      setUploadingState(false);
    }
  };

  const handleDeleteFile = (id: string) => async () => {
    const newUploadedFiles = filesToUpload.map((file) => (file.id === id ? { ...file, isRemoved: true } : file));
    const newUploadedFilesIds = newUploadedFiles
      .filter((file) => !file.isRemoved)
      .map((file) => `[${file.name}](${file.url})`);

    setFilesToUploadState(newUploadedFiles);
    editField({ value: newUploadedFilesIds, attachments: newUploadedFiles });
  };
  const fieldNameErrorMessage = validateKickoffFieldName(name) || '';
  const isKickoffFieldNameValid = !fieldNameErrorMessage;

  const handleOpenUploadWindow = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    uploadFieldRef.current?.click();
  };

  if (mode === EExtraFieldMode.Kickoff) {
    return (
      <div className={styles['extra-field-file__conteiner--template']}>
        <div className={styles['extra-field-file__input--template']}>
          <AutosizeInput
            inputRef={(ref) => {
              fieldNameInputRef.current = ref;
            }}
            inputClassName={classnames(
              styles['extra-field-file__input-name--template'],
              !isKickoffFieldNameValid && styles['extra-field-file__input-name-error--template'],
            )}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            type="text"
            value={name}
            disabled={isDisabled}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                setIsFocused(false);
                event.currentTarget.blur();
              }
            }}
          />
          {isRequired && <span className={kickoffStyles['kick-off-required-sign']} />}
          {!isFocused && (
            <button
              type="button"
              aria-label={namePlaceholder}
              onClick={() => fieldNameInputRef.current?.focus()}
              className={classnames(
                kickoffStyles['kick-off-edit-name'],
                styles['extra-field-file__edit-name-button--template'],
              )}
            >
              <PencilSmallIcon />
            </button>
          )}
        </div>

        {!isKickoffFieldNameValid && (
          <p className={styles['extra-field-file__error-message--template']}>
            <IntlMessages id={fieldNameErrorMessage} />
          </p>
        )}
        <div className={styles['extra-field-file__upload-button-conteiner']}>
          <Button
            label={formatMessage({ id: 'file-upload.label-upload-button' })}
            size="sm"
            buttonStyle="transparent-black"
            disabled
            className={styles['extra-field-file__upload-button--template']}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={styles['extra-field-file__container']} data-autofocus-first-field>
      <div>
        <div className={styles['extra-field-file__field-name']}>{name}</div>
        {isRequired && <span className={kickoffStyles['kick-off-required-sign']} />}
      </div>

      <ExtraFieldFilesGrid
        attachments={filesToUpload}
        deleteFile={handleDeleteFile}
        isUploading={isUploading}
        isEdit
      />

      <input
        className={styles['extra-field-file__ref']}
        multiple
        onChange={handleUploadFile}
        ref={uploadFieldRef}
        type="file"
      />
      <div className={styles['extra-field-file__upload-button-conteiner']}>
        <Button
          label={formatMessage({ id: 'file-upload.label-upload-button' })}
          size="sm"
          buttonStyle="transparent-black"
          onClick={handleOpenUploadWindow}
        />
      </div>
    </div>
  );
}

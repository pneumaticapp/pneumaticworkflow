/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { EExtraFieldMode } from '../../../../types/template';
import { PencilSmallIcon } from '../../../icons';
import { TUploadedFile, uploadFiles } from '../../../../utils/uploadFiles';
import { NotificationManager } from '../../../UI/Notifications';
import { ExtraFieldFilesGrid } from './ExtraFieldFilesGrid';
import { logger } from '../../../../utils/logger';

import { IWorkflowExtraFieldProps } from '..';
import AutosizeInput from 'react-input-autosize';
import { validateKickoffFieldName } from '../../../../utils/validators';
import { IntlMessages } from '../../../IntlMessages';
import kickoffStyles from '../../KickoffRedux/KickoffRedux.css';
import styles from './ExtraFieldFile.css';
import { Button } from '../../../UI/Buttons/Button';
import { useIntl } from 'react-intl';

export function ExtraFieldFile({
  field,
  field: { name, isRequired },
  intl,
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  accountId,
}: IWorkflowExtraFieldProps) {
  const { useCallback, useState, useEffect, createRef } = React;
  const [isUploading, setUploadingState] = useState(false);
  const [filesToUpload, setFilesToUploadState] = useState<TUploadedFile[]>(field.attachments || []);
  const fieldNameInputRef = React.useRef<HTMLInputElement | null>(null);
  const [isFocused, setIsFocused] = React.useState(false);
  const { formatMessage } = useIntl();
  useEffect(() => {
    const { current } = uploadFieldRef;

    if (current && current.value) {
      current.value = '';
    }
  }, [filesToUpload]);

  const uploadFieldRef = createRef<HTMLInputElement>();

  const handleChangeName = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      editField({ name: e.target.value });
    },
    [editField],
  );
  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = e.target;

    if (!files) {
      return;
    }

    try {
      setUploadingState(true);
      const uploadedFiles = await uploadFiles(files, accountId);
      const newUploadedFiles = [...filesToUpload, ...(uploadedFiles as TUploadedFile[])];
      const newUploadedFilesIds = newUploadedFiles.filter((file) => !file.isRemoved).map((file) => String(file.id));

      setFilesToUploadState(newUploadedFiles);
      editField({ value: newUploadedFilesIds, attachments: newUploadedFiles });
    } catch (error) {
      NotificationManager.warning({ message: 'workflows.tasks-failed-to-upload-files' });
      logger.error(error);
    } finally {
      setUploadingState(false);
    }
  };

  const handleDeleteFile = (id: number) => async () => {
    const newUploadedFiles = filesToUpload.map((file) => (file.id === id ? { ...file, isRemoved: true } : file));
    const newUploadedFilesIds = newUploadedFiles.filter((file) => !file.isRemoved).map((file) => String(file.id));

    setFilesToUploadState(newUploadedFiles);
    editField({ value: newUploadedFilesIds, attachments: newUploadedFiles });
  };
  const fieldNameErrorMessage = validateKickoffFieldName(name) || '';
  const isKickoffFieldNameValid = !Boolean(fieldNameErrorMessage);

  const renderKickoffView = () => (
    <div className={styles['extra-field-file__conteiner--template']}>
      <div className={styles['extra-field-file__input--template']}>
        <AutosizeInput
          inputRef={(ref) => (fieldNameInputRef.current = ref)}
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
        {!isFocused && mode === EExtraFieldMode.Kickoff && (
          <button
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

  const handleOpenUploadWindow = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    if (!uploadFieldRef.current) {
      return;
    }

    uploadFieldRef.current.click();
  };

  const renderProcessView = () => {
    return (
      <div className={styles['extra-field-file__container']} data-autofocus-first-field={true}>
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
  };

  const renderFileField = () => {
    const fieldsMap: { [key in EExtraFieldMode]: React.ReactNode } = {
      [EExtraFieldMode.Kickoff]: renderKickoffView(),
      [EExtraFieldMode.ProcessRun]: renderProcessView(),
    };

    return fieldsMap[mode];
  };

  return renderFileField();
}

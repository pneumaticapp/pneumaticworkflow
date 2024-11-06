/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { getFieldValidator } from '../utils/getFieldValidator';
import { EExtraFieldMode } from '../../../../types/template';
import { FieldWithName } from '../utils/FieldWithName';
import { FolderIcon } from '../../../icons';
import { TUploadedFile, uploadFiles } from '../../../../utils/uploadFiles';
import { NotificationManager } from '../../../UI/Notifications';
import { ExtraFieldFilesGrid } from './ExtraFieldFilesGrid';
import { logger } from '../../../../utils/logger';

import { IWorkflowExtraFieldProps } from '..';

import styles from './ExtraFieldFile.css';

export function ExtraFieldFile({
  field,
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
  accountId,
}: IWorkflowExtraFieldProps) {
  const { useCallback, useState, useEffect, createRef } = React;
  const [isUploading, setUploadingState] = useState(false);
  const [filesToUpload, setFilesToUploadState] = useState<TUploadedFile[]>(field.attachments || []);

  useEffect(() => {
    const { current } = uploadFieldRef;

    if (current && current.value) {
      current.value = '';
    }
  }, [filesToUpload]);

  const uploadFieldRef = createRef<HTMLInputElement>();

  const handleChangeName = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    editField({ name: e.target.value });
  }, [editField]);

  const handleChangeDescription = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    editField({ description: e.target.value });
  }, [editField]);

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = e.target;

    if (!files) {
      return;
    }

    try {
      setUploadingState(true);
      const uploadedFiles = await uploadFiles(files, accountId);
      const newUploadedFiles = [...filesToUpload, ...uploadedFiles as TUploadedFile[]];
      const newUploadedFilesIds = newUploadedFiles
        .filter(file => !file.isRemoved)
        .map(file => String(file.id));

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
    const newUploadedFiles = filesToUpload.map(file => file.id === id ? { ...file, isRemoved: true } : file);
    const newUploadedFilesIds = newUploadedFiles
      .filter(file => !file.isRemoved)
      .map(file => String(file.id));

    setFilesToUploadState(newUploadedFiles);
    editField({ value: newUploadedFilesIds, attachments: newUploadedFiles });
  };

  const renderKickoffView = () => (
    <FieldWithName
      field={field}
      descriptionPlaceholder={descriptionPlaceholder}
      namePlaceholder={namePlaceholder}
      mode={mode}
      handleChangeName={handleChangeName}
      labelBackgroundColor={labelBackgroundColor}
      handleChangeDescription={handleChangeDescription}
      validate={getFieldValidator(field, mode)}
      icon={<FolderIcon />}
      isDisabled={isDisabled}
      innerRef={innerRef}
    />
  );

  const handleOpenUploadWindow = () => {
    if (!uploadFieldRef.current) {
      return;
    }

    uploadFieldRef.current.click();
  };

  const renderProcessView = () => {
    return (
      <div className={styles['extra-field-file__container']} data-autofocus-first-field={true}>
        <input
          className={styles['extra-field-file__ref']}
          multiple
          onChange={handleUploadFile}
          ref={uploadFieldRef}
          type="file"
        />
        <FieldWithName
          field={field}
          descriptionPlaceholder={descriptionPlaceholder}
          namePlaceholder={namePlaceholder}
          mode={mode}
          handleChangeName={handleChangeName}
          handleChangeDescription={handleChangeDescription}
          validate={getFieldValidator(field, mode)}
          icon={<FolderIcon />}
          labelBackgroundColor={labelBackgroundColor}
          shouldReplaceWithLabel
          isDisabled
          onClick={handleOpenUploadWindow}
          inputClassName={styles['extra-field-file__input']}
        />
        <ExtraFieldFilesGrid
          attachments={filesToUpload}
          deleteFile={handleDeleteFile}
          isUploading={isUploading}
          isEdit
        />
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

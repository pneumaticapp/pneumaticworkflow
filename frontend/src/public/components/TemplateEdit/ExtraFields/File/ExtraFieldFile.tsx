import React, { ChangeEvent, useCallback, useEffect, useRef, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EFieldLabelPosition } from '../../../../types/fieldset';
import { EExtraFieldMode } from '../../../../types/template';
import { TUploadedFile, uploadFiles } from '../../../../utils/uploadFiles';
import { parseMarkdownToFiles } from '../../../../utils/parseMarkdownFiles';
import { logger } from '../../../../utils/logger';
import { Button } from '../../../UI/Buttons/Button';
import { FieldLabel } from '../utils/FieldLabel';
import { NotificationManager } from '../../../UI/Notifications';
import { IWorkflowExtraFieldProps } from '../types';
import { ExtraFieldFilesGrid } from './ExtraFieldFilesGrid';
import { ExtraFieldFileTemplate } from './ExtraFieldFileTemplate';
import kickoffStyles from '../../KickoffRedux/KickoffRedux.css';

import styles from './ExtraFieldFile.css';

export function ExtraFieldFile({
  field,
  intl,
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  labelBackgroundColor,
  labelPosition,
  onUploadStateChange,
}: IWorkflowExtraFieldProps) {
  const { formatMessage } = useIntl();
  const getFieldFiles = useCallback(
    (): TUploadedFile[] => field.attachments?.length
      ? field.attachments
      : parseMarkdownToFiles(field.markdownValue),
    [field.attachments, field.markdownValue],
  );
  const [filesToUpload, setFilesToUpload] = useState<TUploadedFile[]>(getFieldFiles);
  const [isUploading, setIsUploading] = useState(false);
  const filesToUploadRef = useRef<TUploadedFile[]>(getFieldFiles());
  const uploadFieldRef = useRef<HTMLInputElement>(null);
  const isMountedRef = useRef(true);
  const isUploadingRef = useRef(false);
  const onUploadStateChangeRef = useRef(onUploadStateChange);

  useEffect(() => {
    onUploadStateChangeRef.current = onUploadStateChange;
  }, [onUploadStateChange]);

  useEffect(() => {
    const nextFiles = getFieldFiles();
    filesToUploadRef.current = nextFiles;
    setFilesToUpload(nextFiles);
  }, [getFieldFiles]);

  useEffect(() => {
    if (uploadFieldRef.current?.value) {
      uploadFieldRef.current.value = '';
    }
  }, [filesToUpload]);

  useEffect(
    () => () => {
      isMountedRef.current = false;
      if (isUploadingRef.current) {
        onUploadStateChangeRef.current?.(false);
      }
    },
    [],
  );

  const setUploadingState = (nextIsUploading: boolean) => {
    isUploadingRef.current = nextIsUploading;
    setIsUploading(nextIsUploading);
    onUploadStateChangeRef.current?.(nextIsUploading);
  };

  const updateFieldFiles = (attachments: TUploadedFile[]) => {
    const value = attachments
      .filter((file) => !file.isRemoved)
      .map((file) => `[${file.name}](${file.url})`);

    filesToUploadRef.current = attachments;
    setFilesToUpload(attachments);
    editField({ value, attachments });
  };

  const handleUploadFile = async ({ target: { files } }: ChangeEvent<HTMLInputElement>) => {
    if (!files || isDisabled || isUploadingRef.current) {
      return;
    }

    setUploadingState(true);
    try {
      const uploadedFiles = await uploadFiles(files);
      if (!isMountedRef.current) {
        return;
      }

      const successfulFiles = uploadedFiles.filter((file) => !file.error) as TUploadedFile[];
      updateFieldFiles([...filesToUploadRef.current, ...successfulFiles]);
    } catch (error) {
      if (isMountedRef.current) {
        NotificationManager.warning({ message: 'workflows.tasks-failed-to-upload-files' });
        logger.error(error);
      }
    } finally {
      if (isMountedRef.current) {
        setUploadingState(false);
      }
    }
  };

  const handleDeleteFile = (id: string) => () => {
    if (isDisabled) {
      return;
    }

    updateFieldFiles(
      filesToUploadRef.current.map((file) => (file.id === id ? { ...file, isRemoved: true } : file)),
    );
  };

  if (mode === EExtraFieldMode.Kickoff) {
    return (
      <ExtraFieldFileTemplate
        field={field}
        isDisabled={isDisabled}
        namePlaceholder={namePlaceholder}
        labelPosition={labelPosition}
        editField={editField}
      />
    );
  }

  const isLabelLeft = labelPosition === EFieldLabelPosition.Left;

  return (
    <div
      className={classnames(
        styles['extra-field-file__container'],
        isLabelLeft && kickoffStyles['kick-off-input__field_label-left'],
      )}
      data-autofocus-first-field
    >
      {isLabelLeft ? (
        <FieldLabel
          name={field.name}
          isRequired={field.isRequired || false}
          isDisabled={isDisabled}
          mode={mode}
          labelBackgroundColor={labelBackgroundColor}
          handleChangeName={(event) => editField({ name: event.target.value })}
          className={kickoffStyles['kick-off-input__name_label-left_aligned-start']}
        />
      ) : (
        <div>
          <div className={styles['extra-field-file__field-name']}>{field.name}</div>
          {field.isRequired && <span className={kickoffStyles['kick-off-required-sign']} />}
        </div>
      )}
      <div {...(isLabelLeft && { className: styles['file-content-wrapper_label-left'] })}>
        <ExtraFieldFilesGrid
          attachments={filesToUpload}
          deleteFile={handleDeleteFile}
          isUploading={isUploading}
          isEdit={!isDisabled}
        />
        <input
          className={styles['extra-field-file__ref']}
          disabled={isDisabled || isUploading}
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
            disabled={isDisabled || isUploading}
            onClick={(event) => {
              event.preventDefault();
              uploadFieldRef.current?.click();
            }}
          />
        </div>
      </div>
    </div>
  );
}

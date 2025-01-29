/* eslint-disable jsx-a11y/label-has-associated-control */
import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { TForegroundColor } from '../common/types';
import { getForegroundClass } from '../common/utils/getForegroundClass';
import { FolderIcon } from '../../../icons';
import { TUploadedFile, uploadFiles } from '../../../../utils/uploadFiles';
import { NotificationManager } from "../../Notifications";
import { logger } from '../../../../utils/logger';
import { ExtraFieldFilesGrid } from '../../../TemplateEdit/ExtraFields/File/ExtraFieldFilesGrid';
import { TAttachmentType } from '../../../../types/attachments';
import { isArrayWithItems } from '../../../../utils/helpers';

import { getImageDimensions } from './utils/getImageDimensions';

import styles from './AttachmentField.css';
import commonStyles from '../common/styles.css';

type TInputFieldSize = 'sm' | 'md' | 'lg';

export interface IAttachmentFieldProps {
  title?: string;
  fieldSize?: TInputFieldSize;
  foregroundColor?: TForegroundColor;
  errorMessage?: string;
  isRequired?: boolean;
  containerClassName?: string;
  inputRef?: React.RefObject<HTMLInputElement>;
  accountId: number;
  className?: string;
  uploadedFiles: TUploadedFile[];
  isMultiple?: boolean;
  canDeleteUploadedFiles?: boolean;
  description?: string;
  expectedImageWidth?: number;
  expectedImageHeight?: number;
  acceptedType?: TAttachmentType;
  setUploadedFiles(files: TUploadedFile[]): void;
}

const inputContainerSizeClassMap: { [key in TInputFieldSize]: string } = {
  sm: styles['container_sm'],
  md: styles['container_md'],
  lg: styles['container_lg'],
};

const inputAcceptedTypesMap: { [key in TAttachmentType]: string | undefined } = {
  file: undefined,
  image: 'image/*',
  video: 'video/*',
};

export function AttachmentField({
  inputRef: inputRefProp,
  className,
  title,
  fieldSize = 'lg',
  foregroundColor = 'white',
  errorMessage,
  isRequired,
  containerClassName,
  accountId,
  uploadedFiles,
  isMultiple = false,
  canDeleteUploadedFiles = true,
  description,
  expectedImageWidth,
  expectedImageHeight,
  acceptedType,
  setUploadedFiles,
  // tslint:disable-next-line: trailing-comma
  ...props
}: IAttachmentFieldProps) {
  const { messages, formatMessage } = useIntl();
  const inputRef = inputRefProp || React.useRef(null);
  const normalizedErrorMessage = errorMessage && (messages[errorMessage] || errorMessage);
  const uploadFieldRef = React.createRef<HTMLInputElement>();
  const [isUploading, setUploadingState] = React.useState(false);
  const [filesToUploadState, setFilesToUploadState] = React.useState<TUploadedFile[]>(uploadedFiles);

  React.useEffect(() => {
    // clear file input value after uploading
    const { current } = uploadFieldRef;

    if (current && current.value) {
      current.value = '';
    }
  }, [filesToUploadState]);

  const fileName = React.useMemo(() => {
    if (isMultiple) {
      return '';
    }

    return filesToUploadState.some(file => !file.isRemoved)
      ? filesToUploadState[0].name
      : '';
  }, [filesToUploadState[0]]);

  const handleOpenUploadWindow = () => {
    if (!uploadFieldRef.current) {
      return;
    }

    uploadFieldRef.current.click();
  };

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = e.target;

    if (!files) {
      return;
    }

    const validators = [
      async (file: File | Blob) => {
        try {
          const { width, height } = await getImageDimensions(file);
          if (width !== expectedImageWidth || height !== expectedImageHeight) {
            return formatMessage(
              { id: 'file-upload.wrong-dimension' },
              {
                width,
                height,
                expectedWidth: expectedImageWidth,
                expectedHeight: expectedImageHeight,
              }
            );
          }

          return '';
        } catch (error) {
          return error.message;
        }
      }
    ];

    try {
      setUploadingState(true);
      const newUploadedFiles = await uploadFiles(files, accountId, validators);

      const allFiles = isMultiple || !isArrayWithItems(newUploadedFiles)
        ? [...filesToUploadState, ...newUploadedFiles as TUploadedFile[]]
        : [...newUploadedFiles];
      setFilesToUploadState(allFiles);
      setUploadedFiles(allFiles);
    } catch (error) {
      NotificationManager.warning({ message: 'workflows.tasks-failed-to-upload-files' });
      logger.error(error);
    } finally {
      setUploadingState(false);
    }
  };

  const handleDeleteFile = (id: number) => async () => {
    const newUploadedFiles = filesToUploadState.map(file => file.id === id ? { ...file, isRemoved: true } : file);
    setFilesToUploadState(newUploadedFiles);
    setUploadedFiles(newUploadedFiles);
  };

  const renderInput = () => {
    const inputClassName = classnames(
      styles['input-field'],
      styles['input-field_with-icon'],
      errorMessage && styles['input-field_error'],
      className,
    );

    const input = (
      <button type="button" onClick={handleOpenUploadWindow} className={styles['upload-button']}>
        <input
          ref={inputRef}
          type="text"
          className={inputClassName}
          disabled
          data-testid="input-field"
          value={fileName}
          {...props}
        />
      </button>
    );

    const renderRightContent = () => {
      return <div className={styles['icon']}><FolderIcon /></div>
    }

    return (
      <div className={styles['input-with-rigt-content-wrapper']}>
        {input}

        {renderRightContent()}
      </div>
    );
  };

  const titleClassNames = classnames(
    styles['title'],
    getForegroundClass(foregroundColor),
    isRequired && commonStyles['title_required'],
  );

  return (
    <div
      className={classnames(
        styles['container'],
        inputContainerSizeClassMap[fieldSize],
        title && styles['container_with-title'],
        containerClassName,
      )}
    >
      <input
        className={styles['input-file-trigger']}
        multiple={isMultiple}
        onChange={handleUploadFile}
        ref={uploadFieldRef}
        type="file"
        accept={acceptedType ? inputAcceptedTypesMap[acceptedType] : undefined}
      />
      {renderInput()}
      {title && (
        <span className={titleClassNames}>
          {title}
        </span>
      )}
      {normalizedErrorMessage && (
        <p className={styles['error-text']}>
          {normalizedErrorMessage}
        </p>
      )}

      {description && (
        <p className={styles['field-description']}>
          {description}
        </p>
      )}

      <ExtraFieldFilesGrid
        attachments={filesToUploadState}
        deleteFile={handleDeleteFile}
        isUploading={isUploading}
        isEdit={canDeleteUploadedFiles}
      />
    </div>
  );
}

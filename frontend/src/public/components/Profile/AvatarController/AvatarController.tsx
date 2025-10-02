/* eslint-disable max-len */
/* eslint-disable no-param-reassign */
import React, { useEffect, useState, useRef, ComponentProps } from 'react';
import classnames from 'classnames';
import { useDispatch } from 'react-redux';
// tslint:disable-next-line: match-default-export-name
import AvatarUploader from 'react-avatar-controller';
import { useIntl } from 'react-intl';
import { debounce } from 'throttle-debounce';

import { base64ToBlob } from './utils/base64ToBlob';
import { blobToBase64 } from './utils/blobToBase64';

import { IAuthUser } from '../../../types/redux';
import { Avatar, Modal, Button, Header } from '../../UI';
import { BrowseIcon, DeleteBoldIcon } from '../../icons';
import { useDidUpdateEffect } from '../../../hooks/useDidUpdateEffect';
import { createUUID } from '../../../utils/createId';
import { deleteUserPhoto, uploadUserPhoto } from '../../../redux/actions';
import { MAX_FILE_SIZE } from '../../../utils/uploadFiles';
import { NotificationManager } from '../../UI/Notifications';

import styles from './AvatarController.css';

interface IAvatarControllerProps {
  user: IAuthUser;
  containerClassname?: string;
}

export function AvatarController({ user, containerClassname }: IAvatarControllerProps) {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [uploaderUUID, setUploaderUUID] = useState(createUUID());
  const [croppedPhoto, setCroppedPhoto] = useState<string | null>(null);
  const [initialPhotoBlob, setInitialPhotoBlob] = useState<Blob | undefined>();
  const [photoSrc, setPhotoSrc] = useState<string>('');
  const [uploaderSize, setUploaderSize] = useState(0);
  const modaContentRef = useRef<HTMLDivElement | null>(null);
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const onClose = () => {
    setPhotoSrc('');
    setInitialPhotoBlob(undefined);
    setCroppedPhoto(null);
  };

  useEffect(() => {
    const handleResize = debounce(300, () => {
      setUploaderSize(modaContentRef.current?.clientWidth || 0);
    });

    window.addEventListener('resize', handleResize);
    handleResize();

    if (!isUploadModalOpen) {
      onClose();
    }

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [isUploadModalOpen]);

  useDidUpdateEffect(() => {
    remountUploader();

    async function remountUploader() {
      if (!photoSrc && initialPhotoBlob) {
        setPhotoSrc(await blobToBase64(initialPhotoBlob));
      }

      // setting new key for AvatarUploader in case uploaderSize is changed
      // it helps to reset canvas settings, otherwise the canvas size doesn't update
      setUploaderUUID(createUUID());
    }
  }, [uploaderSize]);

  const uploadPhoto = () => {
    if (!croppedPhoto) {
      return;
    }

    const photoBlob = base64ToBlob(croppedPhoto);

    dispatch(
      uploadUserPhoto({
        photo: photoBlob,
        onComplete: () => setIsUploadModalOpen(false),
      }),
    );
  };

  const getUploaderProps = (): ComponentProps<typeof AvatarUploader> => {
    function onBeforeFileLoad(event: React.ChangeEvent<HTMLInputElement>) {
      const fileSize = event.target.files?.[0]?.size || 0;

      if (fileSize > MAX_FILE_SIZE) {
        NotificationManager.warning({ message: 'file-upload.max-file-size-error' });

        event.target.value = '';
      }
    }

    function onFileLoad(data: File) {
      setInitialPhotoBlob(data);
    }

    return {
      src: photoSrc,
      width: uploaderSize,
      height: uploaderSize,
      imageWidth: uploaderSize,
      containerClassname: styles['avatar-uploader'],
      borderStyle: {
        backgroundImage: `url("data:image/svg+xml,%0A%3Csvg width='${uploaderSize}' height='${uploaderSize}' viewBox='0 0 ${uploaderSize} ${uploaderSize}' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Crect x='0.5' y='0.5' width='${
          uploaderSize - 1
        }' height='${uploaderSize - 1}' rx='15.5' stroke='%23979795' stroke-dasharray='8 8'/%3E%3C/svg%3E%0A")`,
      },
      label: (
        <div className={styles['avatar-uploader_browse-button']}>
          <BrowseIcon className={styles['avatar-uploader_browse-button-icon']} />
          <span>{formatMessage({ id: 'user.avatar.choose-file' })}</span>
        </div>
      ),
      labelStyle: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        height: '100%',
        cursor: 'pointer',
      } as React.CSSProperties,
      closeButtonStyle: {
        position: 'absolute',
        zIndex: 999,
        cursor: 'pointer',
        right: '8px',
        top: '8px',
      } as React.CSSProperties,
      closeIcon: <DeleteBoldIcon className={styles['close']} />,
      onCrop: setCroppedPhoto,
      onBeforeFileLoad,
      onFileLoad,
      onClose,
    };
  };

  const renderUploadModal = () => {
    return (
      <Modal isOpen={isUploadModalOpen} onClose={() => setIsUploadModalOpen(false)}>
        <Header tag="p" size="6" className={styles['modal-title']}>
          {formatMessage({ id: 'user.avatar.upload-title' })}
        </Header>
        <div ref={modaContentRef}>
          <AvatarUploader key={uploaderUUID} {...getUploaderProps()} />

          <Button
            buttonStyle="yellow"
            label={formatMessage({ id: 'user.avatar.apply-changes' })}
            className={styles['apply-button']}
            size="md"
            disabled={!croppedPhoto}
            onClick={uploadPhoto}
          />
        </div>
      </Modal>
    );
  };

  const renderDeleteModal = () => {
    const onDelete = () => {
      dispatch(deleteUserPhoto());
      setIsDeleteModalOpen(false);
    };

    return (
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <Header tag="p" size="6" className={styles['modal-title']}>
          {formatMessage({ id: 'user.avatar.delete-title' })}
        </Header>

        <p className={styles['delete-modal-text']}>{formatMessage({ id: 'user.avatar.delete-text' })}</p>

        <div className={styles['delete-modal-buttons']}>
          <Button
            buttonStyle="yellow"
            label={formatMessage({ id: 'user.avatar.delete-approve' })}
            size="md"
            onClick={onDelete}
          />
          <button
            type="button"
            onClick={() => setIsDeleteModalOpen(false)}
            className={classnames('cancel-button', styles['cancel-delete-button'])}
          >
            {formatMessage({ id: 'user.avatar.delete-cancel' })}
          </button>
        </div>
      </Modal>
    );
  };

  const renderAvatarControl = () => {
    return (
      <div className={styles['control-buttons']}>
        <button type='button' className={styles['control-button']} onClick={() => setIsUploadModalOpen(true)}>
          {formatMessage({ id: 'user.avatar.add' })}
        </button>
        {user.photo && (
          <>
            <div className={styles['control-button-separator']} />
            <button type='button' className={styles['control-button']} onClick={() => setIsDeleteModalOpen(true)}>
              {formatMessage({ id: 'user.avatar.delete' })}
            </button>
          </>
        )}
      </div>
    );
  };

  return (
    <div className={classnames(styles['container'], containerClassname)}>
      <Avatar containerClassName={styles['avatar']} size="xxl" user={user} />
      {renderAvatarControl()}
      {renderUploadModal()}
      {renderDeleteModal()}
    </div>
  );
}

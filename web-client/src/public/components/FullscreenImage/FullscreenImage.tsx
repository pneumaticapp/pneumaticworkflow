/* eslint-disable */
/* prettier-ignore */
import { UnregisterCallback } from 'history';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import InnerImageZoom from 'react-inner-image-zoom';
import * as classnames from 'classnames';

import { history } from '../../utils/history';
import { ClearIcon } from '../icons';
import { Button } from '../UI';

import 'react-inner-image-zoom/lib/InnerImageZoom/styles.min.css';
import styles from './FullscreenImage.css';

export interface IFullscreenImageProps {
  url: string;
  closeFullscreenImage(): void;
}

export function FullscreenImage({ url, closeFullscreenImage }: IFullscreenImageProps) {
  const imageRef = React.useRef<HTMLImageElement>();
  const [isZoomAvaiable, setIsZoomAvailableState] = React.useState(false);

  const unregisterHistoryListener = React.useRef<UnregisterCallback | null>(null);
  const onKeyDown = React.useCallback(({ key }) => {
    if (key === 'Escape') {
      closeFullscreenImage();
    }
  }, []);

  const updateZoomAvailability = React.useCallback(() => {
    if (!imageRef.current) {
      return;
    }
    const { naturalWidth, width } = imageRef.current;
    setIsZoomAvailableState(naturalWidth > width);
  }, []);

  React.useEffect(() => {
    unregisterHistoryListener.current = history.listen(() => {
      closeFullscreenImage();
    });
    document.addEventListener('keydown', onKeyDown);
    document.body.style.overflow = 'hidden';

    const image = document.getElementsByClassName(styles['image'])[0];
    if (image) {
      imageRef.current = image as HTMLImageElement;
      imageRef.current.onload = updateZoomAvailability;
    }
    window.addEventListener('resize', updateZoomAvailability);

    return () => {
      unregisterHistoryListener.current?.();
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = 'unset';
      window.removeEventListener('resize', updateZoomAvailability);
    };
  }, []);

  const renderImage = () => (
    <>
      <div className={styles['backdrop']} onClick={closeFullscreenImage} />
      <div className={styles['container']}>
        <InnerImageZoom
          src={url}
          className={styles['image-container']}
          imgAttributes={{
            className: classnames(
              styles['image'],
              !isZoomAvaiable && styles['image_disable-zoom'],
            ),
            onClick: event => {
              if (!isZoomAvaiable) {
                event.stopPropagation();
              }
            },
          }}
          hideCloseButton
          hideHint
        />
      </div>

      <Button
        onClick={closeFullscreenImage}
        icon={ClearIcon}
        className={styles['close']}
        buttonStyle="black"
        size="md"
      />
    </>
  );

  if (!url) {
    return null;
  }

  return ReactDOM.createPortal(renderImage(), document.body);
}

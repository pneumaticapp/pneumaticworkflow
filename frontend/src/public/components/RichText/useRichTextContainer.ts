import * as React from 'react';
import { useDispatch } from 'react-redux';

import { openFullscreenImage } from '../../redux/general/actions';
import styles from './RichText.css';

export const useRichTextContainer = (
  containerRef: React.RefObject<HTMLDivElement | null>,
  html: string,
) => {
  const dispatch = useDispatch();

  const handleClick = React.useCallback((event: MouseEvent) => {
    const target = event.target as Element;
    const url = target.getAttribute('src');
    if (target.tagName === 'IMG' && url) {
      event.stopImmediatePropagation();
      dispatch(openFullscreenImage({ url }));
    }
  }, [dispatch]);

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return undefined;
    }

    const images = container.getElementsByTagName('img');
    for (let i = 0; i < images.length; i += 1) {
      const image = images[i];

      if (image.complete && image.naturalWidth > 0) {
        image.classList.remove(styles['loading-image']);
      } else {
        image.classList.add(styles['loading-image']);
        image.onload = () => {
          image.classList.remove(styles['loading-image']);
        };
        image.onerror = () => {
          image.classList.remove(styles['loading-image']);
        };
      }
    }

    container.addEventListener('click', handleClick);

    return () => {
      container.removeEventListener('click', handleClick);
    };
  }, [containerRef, handleClick, html]);
};

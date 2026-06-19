import { useLayoutEffect, useState, type RefObject } from 'react';

export function useRichTextLineClamp(
  elementRef: RefObject<HTMLDivElement | null>,
  maxLines: number | undefined,
  isExpanded: boolean,
  text: string,
): boolean {
  const [isTruncated, setIsTruncated] = useState(false);

  useLayoutEffect(() => {
    if (!maxLines || isExpanded) {
      setIsTruncated(false);

      return undefined;
    }

    const element = elementRef.current;

    if (!element) {
      setIsTruncated(false);

      return undefined;
    }

    const measureTruncation = () => {
      setIsTruncated(element.scrollHeight > element.clientHeight + 1);
    };

    measureTruncation();

    const frameId = requestAnimationFrame(measureTruncation);

    const images = element.getElementsByTagName('img');
    for (let i = 0; i < images.length; i += 1) {
      const image = images[i];
      if (!image.complete) {
        image.addEventListener('load', measureTruncation);
      }
    }

    return () => {
      cancelAnimationFrame(frameId);
      const imgs = element.getElementsByTagName('img');
      for (let i = 0; i < imgs.length; i += 1) {
        imgs[i].removeEventListener('load', measureTruncation);
      }
    };
  }, [elementRef, maxLines, isExpanded, text]);

  return isTruncated;
}

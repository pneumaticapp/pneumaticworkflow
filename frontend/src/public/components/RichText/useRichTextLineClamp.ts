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

    const measureTruncation = () => {
      const element = elementRef.current;

      if (!element) {
        setIsTruncated(false);

        return;
      }

      setIsTruncated(element.scrollHeight > element.clientHeight + 1);
    };

    measureTruncation();

    const frameId = requestAnimationFrame(measureTruncation);

    return () => cancelAnimationFrame(frameId);
  }, [elementRef, maxLines, isExpanded, text]);

  return isTruncated;
}

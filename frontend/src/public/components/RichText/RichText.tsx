import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { useRichTextLineClamp } from './useRichTextLineClamp';
import { useRichTextContainer } from './useRichTextContainer';
import { prepareRichTextHtml } from './utils/prepareRichTextHtml';
import { createRichTextMarkdownIt } from './utils/createRichTextMarkdownIt';
import { sanitizeRichTextHtml } from './utils/sanitizeRichTextHtml';
import { RichTextMoreLink } from './RichTextMoreLink';
import styles from './RichText.css';
import badgeStyles from '../../utils/badge/Badge.css';
import type { IRichTextProps } from './types';

export function RichText({
  text,
  isMarkdownMode = true,
  embedVideos = true,
  variables,
  renderExtensions,
  interactiveChecklists,
  hideIcon,
  maxLines,
  className,
}: IRichTextProps): React.ReactElement | null {
  const { formatMessage } = useIntl();
  const [isRendered, setIsRendered] = React.useState(false);
  const [isExpanded, setIsExpanded] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const safeText = text ?? '';
  const isCollapsed = Boolean(maxLines) && !isExpanded;
  const isTruncated = useRichTextLineClamp(containerRef, maxLines, isExpanded, safeText);
  const containerStyle = maxLines
    ? ({ '--rich-text-line-clamp': maxLines } as React.CSSProperties)
    : undefined;

  const markdownIt = React.useMemo(
    () => createRichTextMarkdownIt({
      embedVideos,
      hideIcon,
      interactiveChecklists,
      checkboxPlaceholderClassName: styles['checkbox-fake-placeholder'],
      videoClassName: styles['video'],
      videoContainerClassName: styles['video-container'],
      mentionClassName: styles['mention'],
      variables,
      formatMessage,
      badgeClassName: badgeStyles['badge'],
      specificityBadgeClassName: badgeStyles['specifity'],
    }),
    [embedVideos, hideIcon, interactiveChecklists, variables, formatMessage],
  );

  const preparedText = React.useMemo(
    () => prepareRichTextHtml(safeText, {
      variables,
      formatMessage,
      mentionClassName: styles['mention'],
      badgeClassName: badgeStyles['badge'],
      specificityBadgeClassName: badgeStyles['specifity'],
      replaceInlineTokens: !isMarkdownMode,
    }),
    [safeText, variables, formatMessage, isMarkdownMode],
  );

  const renderedHtml = React.useMemo(() => {
    const html = isMarkdownMode ? markdownIt.render(preparedText) : preparedText;

    return sanitizeRichTextHtml(html);
  }, [isMarkdownMode, markdownIt, preparedText]);

  useRichTextContainer(containerRef, renderedHtml);

  React.useEffect(() => {
    setIsExpanded(false);
  }, [text]);

  React.useLayoutEffect(() => {
    setIsRendered(true);
  }, []);

  const handleExpand = React.useCallback((
    event: React.MouseEvent<HTMLAnchorElement> | React.KeyboardEvent<HTMLAnchorElement>,
  ) => {
    event.preventDefault();
    setIsExpanded(true);
  }, []);

  if (!text) {
    return null;
  }

  const content = (
    <>
      <div
        ref={containerRef}
        className={classnames(styles['container'], isCollapsed && styles['container_collapsed'], styles['markdown-content'])}
        style={containerStyle}
        /* eslint-disable-next-line react/no-danger */
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
      />
      {isMarkdownMode && isRendered && renderExtensions}
    </>
  );

  const needsWrapper = Boolean(maxLines) || Boolean(className);

  if (needsWrapper) {
    return (
      <div
        className={classnames(
          maxLines && styles['wrapper'],
          className,
          maxLines && isCollapsed && styles['wrapper_collapsed'],
        )}
      >
        {content}
        {isCollapsed && isTruncated && <RichTextMoreLink onExpand={handleExpand} />}
      </div>
    );
  }

  return content;
}

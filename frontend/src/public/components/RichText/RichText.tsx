import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { TTaskVariable } from '../TemplateEdit/types';
import { useRichTextLineClamp } from './useRichTextLineClamp';
import { useRichTextContainer } from './useRichTextContainer';
import { prepareRichTextHtml } from './utils/prepareRichTextHtml';
import { createRichTextRemarkable } from './utils/createRichTextRemarkable';
import { RichTextMoreLink } from './RichTextMoreLink';
import styles from './RichText.css';
import badgeStyles from '../../utils/badge/Badge.css';

export interface IRichTextProps {
  text: string | null;
  isMarkdownMode?: boolean;
  embedVideos?: boolean;
  variables?: TTaskVariable[];
  renderExtensions?: React.ReactNode[];
  interactiveChecklists?: boolean;
  hideIcon?: boolean;
  maxLines?: number;
  className?: string;
}

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
  const [isRendered, setIsRendered] = React.useState(false);
  const [isExpanded, setIsExpanded] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const { formatMessage } = useIntl();

  const safeText = text ?? '';
  const isTruncated = useRichTextLineClamp(containerRef, maxLines, isExpanded, safeText);

  React.useEffect(() => {
    setIsExpanded(false);
  }, [text]);

  React.useLayoutEffect(() => {
    setIsRendered(true);
  }, []);

  const remarkable = React.useMemo(
    () => createRichTextRemarkable({
      embedVideos,
      hideIcon,
      interactiveChecklists,
      checkboxPlaceholderClassName: styles['checkbox-fake-placeholder'],
      videoClassName: styles['video'],
    }),
    [embedVideos, hideIcon, interactiveChecklists],
  );

  const htmlString = React.useMemo(
    () => prepareRichTextHtml(safeText, {
      variables,
      formatMessage,
      mentionClassName: styles['mention'],
      badgeClassName: badgeStyles['badge'],
      specificityBadgeClassName: badgeStyles['specifity'],
    }),
    [safeText, variables, formatMessage],
  );

  const renderedHtml = React.useMemo(
    () => (isMarkdownMode ? remarkable.render(htmlString) : htmlString),
    [isMarkdownMode, remarkable, htmlString],
  );

  useRichTextContainer(containerRef, renderedHtml);

  const handleExpand = React.useCallback((
    event: React.MouseEvent<HTMLAnchorElement> | React.KeyboardEvent<HTMLAnchorElement>,
  ) => {
    event.preventDefault();
    setIsExpanded(true);
  }, []);

  if (!text) {
    return null;
  }

  const isCollapsed = Boolean(maxLines) && !isExpanded;
  const collapsedStyle = isCollapsed && maxLines
    ? ({
      WebkitLineClamp: maxLines,
      lineClamp: maxLines,
    } as React.CSSProperties)
    : undefined;

  const content = (
    <>
      {isMarkdownMode && isRendered && renderExtensions}
      {/* eslint-disable-next-line react/no-danger */}
      <div
        ref={containerRef}
        className={classnames(styles['container'], isCollapsed && styles['container_collapsed'])}
        style={collapsedStyle}
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
      />
    </>
  );

  const needsWrapper = Boolean(maxLines) || Boolean(className);

  if (!needsWrapper) {
    return content;
  }

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

import * as React from 'react';
import ReactDOMServer from 'react-dom/server';

import { DocumentAttachment } from '../../Attachments/DocumentAttachment';
import { ECustomEditorEntities } from '../../RichEditor/utils/types';

interface IRenderAttachmentHtmlOptions {
  url: string;
  name: string;
  entityType: ECustomEditorEntities;
  hideIcon?: boolean;
}

export const renderAttachmentHtml = ({
  url,
  name,
  entityType,
  hideIcon,
}: IRenderAttachmentHtmlOptions): string => {
  const renderMap: Record<ECustomEditorEntities, string> = {
    [ECustomEditorEntities.Link]: `<a href="${url}" target="_blank">${name}</a>`,
    [ECustomEditorEntities.Image]: `<img src=${url} />`,
    [ECustomEditorEntities.Video]: ReactDOMServer.renderToStaticMarkup(
      // eslint-disable-next-line jsx-a11y/media-has-caption
      <video src={url} preload="auto" controls />,
    ),
    [ECustomEditorEntities.File]: ReactDOMServer.renderToStaticMarkup(
      <DocumentAttachment name={name} url={url} isEdit={false} hideIcon={hideIcon} />,
    ),
    [ECustomEditorEntities.Variable]: '',
    [ECustomEditorEntities.Mention]: '',
  };

  return renderMap[entityType];
};

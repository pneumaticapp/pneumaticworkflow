/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import ReactDOMServer from 'react-dom/server';
import * as xssFilters from 'xss-filters';
import { useDispatch } from 'react-redux';
import { Remarkable } from 'remarkable';
import { linkify } from './linkify';

import {
  mentionsRegex,
  youtubeVideoRegexp,
  loomVideoRegexp,
  wistiaVideoRegexp,
  variableRegex,
} from '../../constants/defaultValues';
import { isArrayWithItems } from '../../utils/helpers';
import { TTaskVariable } from '../TemplateEdit/types';
import { truncateString } from '../../utils/truncateString';
import { openFullscreenImage } from '../../redux/general/actions';
import { DocumentAttachment } from '../Attachments/DocumentAttachment';
import {
  linksRemarkablePlugin,
  checklistsRemarkablePlugin,
  TCustomLinkToken,
} from '../RichEditor/utils/сonverters/customMarkdownPlugins';
import { LinkCloseToken } from 'remarkable/lib';
import { ECustomEditorEntities } from '../RichEditor/utils/types';
import { createChecklistRenderer } from '../TaskCard/checklist/createChecklistRenderer';
import { createCheckPlaceholderId } from '../TaskCard/checklist/createCheckPlaceholderId';
import { prepareChecklistsForRendering } from '../../utils/checklists/prepareChecklistsForRendering';
import { createProgressbarPlaceholderId } from '../TaskCard/checklist/createProgressbarPlaceholderId';

import styles from './RichText.css';
import badgeStyles from '../../utils/badge/Badge.css';

export interface IRichTextProps {
  text: string | null;
  isMarkdownMode?: boolean;
  embedVideos?: boolean;
  variables?: TTaskVariable[];
  renderExtensions?: React.ReactNode[];
  interactiveChecklists?: boolean;
}

const MAX_VARIABLE_LENGTH = 20;

export function RichText({
  text,
  isMarkdownMode = true,
  embedVideos = true,
  variables,
  renderExtensions,
  interactiveChecklists,
}: IRichTextProps) {
  if (!text) {
    return null;
  }

  const [isRendered, setIsRendered] = React.useState(false);

  React.useLayoutEffect(() => {
    setIsRendered(true);
  }, []);

  const md = new Remarkable({
    html: true,
    breaks: true,
  })
    .use(checklistsRemarkablePlugin)
    .use(linkify)
    .use(attachmnetRenderer(embedVideos))
    .use(
      createChecklistRenderer({
        renderCheck: (listApiName, itemApiName) => {
          if (interactiveChecklists) {
            return `<div id="${createCheckPlaceholderId(listApiName, itemApiName)}"></div>`;
          }

          return `<div class="${styles['checkbox-fake-placeholder']}"></div>`;
        },
        renderProgressbar: (listApiName) => {
          if (!interactiveChecklists) {
            return '';
          }

          return `<div id="${createProgressbarPlaceholderId(listApiName)}"></div>`;
        },
        interactiveChecklist: interactiveChecklists,
      }),
    );

  const dispatch = useDispatch();
  const conatainerRef = React.useRef<HTMLDivElement>(null);
  const handleClick = React.useCallback((event: MouseEvent) => {
    const target = event.target as Element;
    const url = target.getAttribute('src');
    if (target.tagName === 'IMG' && url) {
      event.stopImmediatePropagation();
      dispatch(openFullscreenImage({ url }));
    }
  }, []);

  const showImagePlaceholders = (container: HTMLDivElement) => {
    const images = container.getElementsByTagName('img');
    for (let i = 0; i < images.length; i++) {
      images[i].classList.add(styles['loading-image']);
      images[i].onload = () => {
        images[i].classList.remove(styles['loading-image']);
      };
    }
  };

  React.useEffect(() => {
    if (conatainerRef.current) {
      showImagePlaceholders(conatainerRef.current);
      conatainerRef.current.addEventListener('click', handleClick);
    }

    return () => {
      if (conatainerRef.current) {
        conatainerRef.current.removeEventListener('click', handleClick);
      }
    };
  }, []);

  const REPLACE_RULES: {
    regExp: RegExp;
    // tslint:disable-next-line: no-any
    replaceLogic: any;
  }[] = [
    {
      // This is a hacky way to correctly render new lines in markdown
      regExp: /\n/g,
      replaceLogic: (match: string, offset: number, str: string) => {
        const nextSymbol = str[offset + 1];

        return nextSymbol === '\n' ? '\n&nbsp;\n' : match;
      },
    },
    {
      regExp: mentionsRegex,
      replaceLogic: `<span class='${styles['mention']}'>@$1</span>`,
    },
    {
      regExp: variableRegex,
      replaceLogic: (match: string, variableApiName: string) => {
        if (!isArrayWithItems(variables)) {
          return match;
        }

        const variable = variables.find((variable) => variableApiName === variable.apiName);
        if (!variable) {
          return match;
        }

        return `<span class="${badgeStyles['badge']} ${badgeStyles['specifity']}">${truncateString(
          variable.title,
          MAX_VARIABLE_LENGTH,
        )}</span>`;
      },
    },
  ];

  const sanitizedText = xssFilters.inHTMLData(prepareChecklistsForRendering(text));

  const htmlString = REPLACE_RULES.reduce((acc, { regExp, replaceLogic }) => {
    const replaceRegex = new RegExp(regExp, 'gi');

    return acc.replace(replaceRegex, replaceLogic);
  }, sanitizedText);

  if (!isMarkdownMode) {
    return <div dangerouslySetInnerHTML={{ __html: htmlString }} />;
  }

  return (
    <>
      {isRendered && renderExtensions}
      <div
        ref={conatainerRef}
        className={styles['container']}
        dangerouslySetInnerHTML={{ __html: md.render(htmlString) }}
      />
    </>
  );
}

const attachmnetRenderer = (embedVideoLinks: boolean) => {
  const renderLink = (url: string, name: string) => {
    const defaultLinkHtml = `<a href="${url}" target="_blank">${name}<a/>`;
    if (!embedVideoLinks) {
      return defaultLinkHtml;
    }

    const renderRules = [
      {
        regExp: loomVideoRegexp,
        replaceLogic: (match: string, group1: string) => {
          return `<div><iframe class="${styles['video']}" frameBorder="0" src="https://www.useloom.com/embed/${group1}" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe></div>`;
        },
      },
      {
        regExp: youtubeVideoRegexp,
        replaceLogic: (match: string, group1: string) => {
          return `<div><iframe class="${styles['video']}" frameBorder="0" src="//www.youtube.com/embed/${group1}" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe></div>`;
        },
      },
      {
        regExp: wistiaVideoRegexp,
        replaceLogic: (match: string, videoId: string) => {
          const videoUrl = `https://fast.wistia.com/embed/medias/${videoId}`;

          return `<div><iframe class="${styles['video']}" allowtransparency="true" frameborder="0" scrolling="no" src="${videoUrl}" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe></div>`;
        },
      },
    ];

    const renderVideoLogic = renderRules.find(({ regExp }) => regExp.test(url));
    if (renderVideoLogic) {
      return url.replace(renderVideoLogic.regExp, renderVideoLogic.replaceLogic);
    }

    return defaultLinkHtml;
  };

  return (md: Remarkable) => {
    md.inline.ruler.disable(['links']);
    md.use(linksRemarkablePlugin, {});

    // @ts-ignore
    md.renderer.rules.link_open = (tokens: TCustomLinkToken[], idx: number) => {
      const url = tokens[idx]['url'];
      const name = tokens[idx]['name'];
      const entityType = tokens[idx]['entityType'];
      const isLinkified = tokens[idx]['isLinkified'];

      if (isLinkified || !entityType) {
        return renderLink(url, name);
      }

      const renderMap: { [key in ECustomEditorEntities]: string } = {
        [ECustomEditorEntities.Link]: `<a href="${url}" target="_blank">`,
        [ECustomEditorEntities.Image]: `<img src=${url} />`,
        [ECustomEditorEntities.Video]: ReactDOMServer.renderToStaticMarkup(<video src={url} preload="auto" controls />),
        [ECustomEditorEntities.File]: ReactDOMServer.renderToStaticMarkup(
          <DocumentAttachment name={name} url={url} isEdit={false} />,
        ),
        [ECustomEditorEntities.Variable]: '',
        [ECustomEditorEntities.Mention]: '',
      };

      return renderMap[entityType];
    };

    // @ts-ignore
    md.renderer.rules.link_close = (tokens: LinkCloseToken[], idx: number) => {
      // @ts-ignore
      const entityType = tokens[idx]['entityType'];
      if (entityType === 'LINK') {
        return '</a>';
      }

      return '';
    };
  };
};

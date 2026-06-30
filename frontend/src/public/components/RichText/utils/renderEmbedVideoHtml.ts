import {
  youtubeVideoRegexp,
  loomVideoRegexp,
  wistiaVideoRegexp,
} from '../../../constants/defaultValues';

export interface IRenderEmbedVideoHtmlOptions {
  videoClassName: string;
  videoContainerClassName: string;
}

interface IEmbedVideoRule {
  regExp: RegExp;
  getEmbedSrc: (match: RegExpMatchArray) => string;
  iframeExtraAttrs?: string;
}

const IFRAME_COMMON_ATTRS = 'webkitallowfullscreen mozallowfullscreen allowfullscreen';

const EMBED_VIDEO_RULES: IEmbedVideoRule[] = [
  {
    regExp: loomVideoRegexp,
    getEmbedSrc: ([, videoId]) => `https://www.useloom.com/embed/${videoId}`,
  },
  {
    regExp: youtubeVideoRegexp,
    getEmbedSrc: ([, videoId]) => `//www.youtube.com/embed/${videoId}`,
  },
  {
    regExp: wistiaVideoRegexp,
    getEmbedSrc: ([, videoId]) => `https://fast.wistia.com/embed/medias/${videoId}`,
    iframeExtraAttrs: 'allowtransparency="true" scrolling="no"',
  },
];

const getVideoUrlMatch = (url: string, regExp: RegExp): RegExpMatchArray | null => {
  const matchRegExp = new RegExp(regExp.source, regExp.flags.replace('g', ''));

  return matchRegExp.exec(url);
};

const renderEmbedIframeHtml = (
  embedSrc: string,
  { videoClassName, videoContainerClassName }: IRenderEmbedVideoHtmlOptions,
  iframeExtraAttrs = '',
): string => {
  const extraAttrs = iframeExtraAttrs ? ` ${iframeExtraAttrs}` : '';

  return (
    `<div class="${videoContainerClassName}">`
    + `<iframe class="${videoClassName}" frameborder="0" src="${embedSrc}" ${IFRAME_COMMON_ATTRS}${extraAttrs}></iframe>`
    + '</div>'
  );
};

export const renderEmbedVideoHtml = (
  url: string,
  options: IRenderEmbedVideoHtmlOptions,
): string | null => {
  const matchedRule = EMBED_VIDEO_RULES.find(({ regExp }) => getVideoUrlMatch(url, regExp));

  if (!matchedRule) {
    return null;
  }

  const match = getVideoUrlMatch(url, matchedRule.regExp);

  if (!match) {
    return null;
  }

  return renderEmbedIframeHtml(
    matchedRule.getEmbedSrc(match),
    options,
    matchedRule.iframeExtraAttrs,
  );
};

export const renderLinkHtml = (
  url: string,
  name: string,
  embedVideos: boolean,
  options: IRenderEmbedVideoHtmlOptions,
): string => {
  if (embedVideos) {
    const embedHtml = renderEmbedVideoHtml(url, options);

    if (embedHtml) {
      return embedHtml;
    }
  }

  return `<a href="${url}" target="_blank">${name}</a>`;
};

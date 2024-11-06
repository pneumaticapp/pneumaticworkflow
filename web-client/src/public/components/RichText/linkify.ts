/* eslint-disable */
/* prettier-ignore */
// @ts-nocheck
// tslint:disable

// This file was copied from https://github.com/jonschlinkert/remarkable/blob/58b6945f203ca7a0bb5a0785df90a3a6a8b9e59c/lib/linkify.js
// and then the link_open token params was changed to correctly work with editor attachments.

import Autolinker from 'autolinker';


let LINK_SCAN_RE = /www|@|\:\/\//;


function isLinkOpen(str) {
  return /^<a[>\s]/i.test(str);
}
function isLinkClose(str) {
  return /^<\/a\s*>/i.test(str);
}

// Stupid fabric to avoid singletons, for thread safety.
// Required for engines like Nashorn.
//
function createLinkifier() {
  let links = [];
  let autolinker = new Autolinker({
    stripPrefix: false,
    url: true,
    email: true,
    replaceFn (match) {
      // Only collect matched strings but don't change anything.
      switch (match.getType()) {
      /*eslint default-case:0*/
      case 'url':
        links.push({
          text: match.matchedText,
          url: match.getUrl(),
        });
        break;
      case 'email':
        links.push({
          text: match.matchedText,
          // normalize email protocol
          url: `mailto:${  match.getEmail().replace(/^mailto:/i, '')}`,
        });
        break;
      }

      return false;
    },
  });

  return {
    links,
    autolinker,
  };
}


function parseTokens(state) {
  let i; let j; let l; let tokens; let token; let text; let nodes; let ln; let pos; let level; let htmlLinkLevel;
  let blockTokens = state.tokens;
  let linkifier = null; let links; let autolinker;

  for (j = 0, l = blockTokens.length; j < l; j++) {
    if (blockTokens[j].type !== 'inline') {
      continue;
    }
    tokens = blockTokens[j].children;

    htmlLinkLevel = 0;

    // We scan from the end, to keep position when new tags added.
    // Use reversed logic in links start/end match
    for (i = tokens.length - 1; i >= 0; i--) {
      token = tokens[i];

      // Skip content of markdown links
      if (token.type === 'link_close') {
        i--;
        while (tokens[i].level !== token.level && tokens[i].type !== 'link_open') {
          i--;
        }
        continue;
      }

      // Skip content of html tag links
      if (token.type === 'htmltag') {
        if (isLinkOpen(token.content) && htmlLinkLevel > 0) {
          htmlLinkLevel--;
        }
        if (isLinkClose(token.content)) {
          htmlLinkLevel++;
        }
      }
      if (htmlLinkLevel > 0) {
        continue;
      }

      if (token.type === 'text' && LINK_SCAN_RE.test(token.content)) {

        // Init linkifier in lazy manner, only if required.
        if (!linkifier) {
          linkifier = createLinkifier();
          links = linkifier.links;
          autolinker = linkifier.autolinker;
        }

        text = token.content;
        links.length = 0;
        autolinker.link(text);

        if (!links.length) {
          continue;
        }

        // Now split string to nodes
        nodes = [];
        level = token.level;

        for (ln = 0; ln < links.length; ln++) {

          if (!state.inline.validateLink(links[ln].url)) {
            continue;
          }

          pos = text.indexOf(links[ln].text);

          if (pos) {
            nodes.push({
              type: 'text',
              content: text.slice(0, pos),
              level,
            });
          }
          nodes.push({
            type: 'link_open',
            url: links[ln].url,
            name: links[ln].text,
            isLinkified: true,
            level: level++,
          });
          nodes.push({
            type: 'link_close',
            level: --level,
          });
          text = text.slice(pos + links[ln].text.length);
        }
        if (text.length) {
          nodes.push({
            type: 'text',
            content: text,
            level,
          });
        }

        // replace current node
        blockTokens[j].children = tokens = [].concat(tokens.slice(0, i), nodes, tokens.slice(i + 1));
      }
    }
  }
};

export function linkify(md) {
  md.core.ruler.push('linkify', parseTokens);
};

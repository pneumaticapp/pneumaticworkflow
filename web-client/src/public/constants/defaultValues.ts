/* eslint-disable no-useless-escape */
/* eslint-disable no-irregular-whitespace */
/* eslint-disable max-len */
import { Config } from 'react-player';

import { TMenuType } from '../types/common';
import { ELocale, ELocaleDirection, ILocaleOption } from '../types/redux';
import { EPayPeriod } from '../types/pricing';
import { envSentry } from './enviroment';

export const defaultMenuType: TMenuType = 'menu-default';

export const NAVBAR_HEIGHT = 104;
export const MOBILE_NAVBAR_HEIGHT = 0;

export const defaultLocale = ELocale.English;

export const localeOptions: ILocaleOption[] = [
  { id: ELocale.English, name: 'English - LTR', direction: ELocaleDirection.LeftToRight },
  { id: ELocale.Russian, name: 'Russian - LTR', direction: ELocaleDirection.LeftToRight },
];

export const DISCOVERY_CALL_URL = 'https://calendly.com/pneumaticworkflow/discovery-call';
export const ZAPIER_EMBED_SCRIPT_SRC = 'https://cdn.zapier.com/packages/partner-sdk/v0/zapier-elements/zapier-elements.esm.js';
export const ZAPIER_EMBED_CSS_HREF = 'https://cdn.zapier.com/packages/partner-sdk/v0/zapier-elements/zapier-elements.css';

export const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,255}$/i;
export const phoneRegex = /^\+?1?\d{9,15}$/;
export const whitespaceRegex = /\s+/i;
export const urlRegex = /((https?|ftp):\/\/)?[a-z0-9.-]+\.[a-z]{2,}(\/\S*?(?=\.*(?:\s|,|$)))?/gi;
export const urlWithProtocolRegex = /((https?|ftp):\/\/)[a-z0-9.-]+\.[a-z]{2,}(\/\S*?(?=\.*(?:\s|,|$)))?/gi;
export const couponRegex = /([A-Za-z0-9\+\-\_])+/;
export const hostNameRegex = /(^https?:\/\/)(www[0-9]?\.)?([^/:]+)/i;
export const mentionsRegex = /\[([^\n\|]+)\|([0-9]+)\]/;
export const variableRegex = /\{\{\s?([а-яa-z0-9\-_]+)\s?\}\}/i;
export const youtubeVideoRegexp = /(?:http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(?:&(?:amp;)?‌​[\w\?‌​=]*)?)/gi;
export const loomVideoRegexp = /(?:https?:\/\/(?:www\.|stage\.)?(?:use)?(?:loom|loomlocal)\.com(?::4444)?\/share\/([a-f0-9]+))(?:\?t=[0-9]*)?/gi;
export const wistiaVideoRegexp = /(?:https?:\/\/)?[a-z0-9]+\.wistia\.com\/medias\/([a-z0-9]+)/gi;
export const imageUrlRegex = /(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png)/gi;

export const DASHBOARD_VIDEO_URL = 'https://pneumaticworkflow.wistia.com/medias/0ph9hqcku3';

export const DEFAULT_VIDEO_PLAYER_CONFIG: Config = {
  wistia: {
    options: {
      frameborder: 0,
      allowtransparency: true,
      playerColor: '#fec336',
      videoFoam: true,
      popover: true,
    },
  },
};

export const enum EColors {
  Primary = '#ff9e01',
  Link = '#FEC336',
  LinkHover = '#E79A26',
  Black100 = '#262522',
  Black72 = '#62625F',
  Black48 = '#979795',
  Black32 = '#B9B9B8',
  Black16 = '#DCDCDB',
  Notification1 = '#FC5B67',
  Notification2 = '#FEE55A',
  Notification3 = '#24D5A1',
  Notification4 = '#3496C9',
  Gray = '#d7d7d7',
  Black = '#010101',
}

export const payTypes = [
  { key: 1, value: EPayPeriod.Monthly, label: 'Billed monthly' },
  { key: 2, value: EPayPeriod.Annually, label: 'Billed annually' },
];

export const PRICE_FREE_USER_IN_USD_MO = 0;

export const PRICE_UNLIMITED_USER_IN_USD_MO = 99;
export const PRICE_UNLIMITED_USER_IN_USD_ANN = 79;

export const PRICE_FRACTIONALCOO_USER_IN_USD_MO = 599;
export const PRICE_FRACTIONALCOO_USER_IN_USD_ANN = 479;

export const USERS_COUNT_IN_FREE_PLAN = 5;
export const ANNUAL_PAYMENT_DISCOUNT = 0.2;

export const enum ETimeouts {
  Short = 5 * 1000,
  Default = 10 * 1000,
  Prolonged = 20 * 1000,
  Long = 5 * 60 * 1000,
}

export const ELLIPSIS_CHAR = '… ';
export const MAX_VISIBLE_ICONS = 5;

export const DEFAULT_TASK_COMMENTS_LIMIT = 5;
export const SHOW_MORE_TASK_COMMENTS_LIMIT = 10;

export const DEV_SENTRY_DSN = envSentry || 'https://2b5bb14eab304481867ba30f6d029a6f@o313255.ingest.sentry.io/5276349';
export const PROD_SENTRY_DSN = envSentry || 'https://4e313a51d19346f094be5417b871b575@o313255.ingest.sentry.io/5433088';

export const ENTER_KEY_CODE = 13;

export const enum EPageTitle {
  MyTasks = 'tasks.title',
  Workflows = 'workflows.title',
  Templates = 'templates.title',
  TemplatesSystem = 'templates.title-system',
  Highlights = 'workflow-highlights.title',
  Integrations = 'integrations.title',
}

export const enum ELearnMoreLinks {
  Tasks = 'https://support.pneumatic.app/en/articles/5920342-video-task-management-in-pneumatic',
  Workflows = 'https://support.pneumatic.app/en/articles/5605999-video-quick-product-overview',
  Templates = '',
  TemplatesSystem = '',
  Highlights = 'https://support.pneumatic.app/en/articles/5249965-how-to-use-workflow-highlights',
  Integrations = 'https://support.pneumatic.app/en/articles/6014550-integrations',
  HowToCreateTemplate = 'https://support.pneumatic.app/en/articles/5534875-how-to-create-your-first-workflow-template',
  GuestUsers = 'https://support.pneumatic.app/en/articles/6145048-free-external-users',
  Checklists = 'https://support.pneumatic.app/en/articles/6145048-free-external-users',
  Tenants = 'https://www.pneumatic.app/partners/',
  TenantsModal = 'https://www.pneumatic.app/partners/',
}

export const GUEST_TOKEN_STORAGE_KEY = 'guestToken';

export const REMARKABLE_DISIBLE_MARKDOWN_OPTIONS = {
  disable: {
    inline: [
      'text',
      'sup',
      'sub',
      'newline',
      'mark',
      'links',
      'ins',
      'htmltag',
      'footnote_ref',
      'footnote_inline',
      'escape',
      'entity',
      'emphasis',
      'del',
      'backticks',
      'autolink',
    ],
    block: [
      'blockquote',
      'code',
      'deflist',
      'fences',
      'footnote',
      'heading',
      'hr',
      'htmlblock',
      'lheading',
      'list',
      'table',
    ],
    core: [
      'abbr',
      'abbr2',
      'footnote_tail',
      'references',
      'replacements',
      'smartquotes',
    ],
  },
};

export const enum EResponseStatuses {
  NotFound = 404,
}

export const LIMIT_LOAD_TEMPLATES = 30;
export const LIMIT_LOAD_SYSTEMS_TEMPLATES = 16;

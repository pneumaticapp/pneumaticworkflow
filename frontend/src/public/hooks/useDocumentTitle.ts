import { useEffect } from 'react';
import { useIntl } from 'react-intl';

import {
  getDocumentTitleSuffix,
  PNEUMATIC_SUFFIX,
  TITLES,
  TITLE_MESSAGE_IDS,
  TDocumentTitle,
} from '../constants/titles';

export function useDocumentTitle(title: TDocumentTitle, content?: string | null): void {
  const { formatMessage, locale } = useIntl();
  const hasSuffix = title !== 'TryForFree';
  const defaultMessage = hasSuffix ? TITLES[title].replace(` ${PNEUMATIC_SUFFIX}`, '') : TITLES[title];
  const text = content ?? formatMessage({ id: TITLE_MESSAGE_IDS[title], defaultMessage });
  const pageTitle = hasSuffix ? `${text} ${getDocumentTitleSuffix(locale)}` : text;

  useEffect(() => {
    document.title = pageTitle;
  }, [pageTitle]);
}

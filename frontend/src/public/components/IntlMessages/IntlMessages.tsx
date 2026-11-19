/* prettier-ignore */
import React from 'react';
import type { IntlShape } from 'react-intl';
import { FormattedMessage, injectIntl } from 'react-intl';

interface IInjectedOptions {
  id: string;
  intl: IntlShape;
}

type TInjectMessageProps = React.ComponentProps<typeof FormattedMessage> & IInjectedOptions;

const InjectMassage = (props: TInjectMessageProps) => <FormattedMessage {...props} tagName={props.tagName || 'span'} />;

export const IntlMessages = injectIntl<'intl', TInjectMessageProps>(InjectMassage, { forwardRef: true });

/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { FormattedMessage, injectIntl, IntlShape } from 'react-intl';

interface IInjectedOptions {
  id: string;
  intl: IntlShape;
}

type TInjectMessageProps = React.ComponentProps<typeof FormattedMessage> & IInjectedOptions;

const InjectMassage = (props: TInjectMessageProps) => <FormattedMessage {...props} tagName={props.tagName || 'span'}/>;

export const IntlMessages = injectIntl<'intl', TInjectMessageProps>(InjectMassage, {forwardRef: true});

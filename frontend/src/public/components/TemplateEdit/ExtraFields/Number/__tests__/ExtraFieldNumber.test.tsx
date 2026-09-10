import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { enMessages } from '../../../../../lang/locales/en_US';

import { ExtraFieldNumber } from '../ExtraFieldNumber';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldType, EExtraFieldMode } from '../../../../../types/template';
import { EFieldLabelPosition, EFieldRuleType } from '../../../../../types/fieldset';
import { createIntl, createIntlCache, IntlProvider } from 'react-intl';

const cache = createIntlCache();
const intl = createIntl({ locale: 'en-US', messages: enMessages }, cache);
const formatMsg = (id: string, values?: Record<string, string | number>) =>
  intl.formatMessage({ id }, values);

const baseProps = {
  field: makeExtraField({ type: EExtraFieldType.Number, apiName: 'num-1', name: 'Numeric field' }),
  intl,
  editField: jest.fn(),
  mode: EExtraFieldMode.Kickoff,
  labelPosition: EFieldLabelPosition.Top,
  accountId: 1,
};

const renderWithIntl = (ui: React.ReactElement) =>
  render(
    <IntlProvider locale="en" messages={enMessages}>
      {ui}
    </IntlProvider>,
  );

describe('ExtraFieldNumber rulesets badge', () => {
  it('does not render rulesets badge when field has no rulesets', () => {
    renderWithIntl(<ExtraFieldNumber {...baseProps} />);

    expect(screen.queryByText(/Rulesets:/)).not.toBeInTheDocument();
  });

  it('does not render rulesets badge when rulesets array is empty', () => {
    const field = makeExtraField({
      type: EExtraFieldType.Number,
      apiName: 'num-1',
      rulesets: [],
    });

    renderWithIntl(<ExtraFieldNumber {...baseProps} field={field} />);

    expect(screen.queryByText(/Rulesets:/)).not.toBeInTheDocument();
  });

  it('renders rulesets badge with correct count when field has rulesets', () => {
    const field = makeExtraField({
      type: EExtraFieldType.Number,
      apiName: 'num-1',
      rulesets: [
        { apiName: 'rs-1', name: 'Rule 1', type: EFieldRuleType.Validator, message: '', groupsOr: [], order: 0 },
        { apiName: 'rs-2', name: 'Rule 2', type: EFieldRuleType.Validator, message: '', groupsOr: [], order: 1 },
      ],
    });

    renderWithIntl(<ExtraFieldNumber {...baseProps} field={field} />);

    expect(screen.getByText(formatMsg('fieldsets.field-rulesets-badge', { count: 2 }))).toBeInTheDocument();
  });

  it('renders rulesets badge with count 1 for a single ruleset', () => {
    const field = makeExtraField({
      type: EExtraFieldType.Number,
      apiName: 'num-1',
      rulesets: [
        { apiName: 'rs-1', name: 'Rule 1', type: EFieldRuleType.Validator, message: '', groupsOr: [], order: 0 },
      ],
    });

    renderWithIntl(<ExtraFieldNumber {...baseProps} field={field} />);

    expect(screen.getByText(formatMsg('fieldsets.field-rulesets-badge', { count: 1 }))).toBeInTheDocument();
  });
});

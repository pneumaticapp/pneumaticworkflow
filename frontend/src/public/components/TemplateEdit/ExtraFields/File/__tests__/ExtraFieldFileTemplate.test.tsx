import * as React from 'react';
import { render } from '@testing-library/react';

import { ExtraFieldFileTemplate } from '../ExtraFieldFileTemplate';
import { FieldLabel } from '../../utils/FieldLabel';
import { FieldsetRulesetsBadge } from '../../../../Fieldsets/FieldsetRulesetsBadge/FieldsetRulesetsBadge';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EFieldLabelPosition, EFieldRuleType } from '../../../../../types/fieldset';

jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
}));

jest.mock('../../../../IntlMessages', () => ({
  IntlMessages: jest.fn(() => null),
}));

jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

jest.mock('../../../../UI/Buttons/Button', () => ({
  Button: jest.fn(() => null),
}));

jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

jest.mock('../../../../Fieldsets/FieldsetRulesetsBadge/FieldsetRulesetsBadge', () => ({
  FieldsetRulesetsBadge: jest.fn(() => React.createElement('span', { 'data-testid': 'rulesets-badge' })),
}));

describe('ExtraFieldFileTemplate', () => {
  const mockEditField = jest.fn();

  const rulesets = [
    { apiName: 'rs-1', name: 'Rule', type: EFieldRuleType.Validator, message: '', groupsOr: [], order: 0 },
  ];

  const baseProps = {
    field: makeExtraField({ name: 'Attachment', rulesets }),
    isDisabled: false,
    namePlaceholder: 'Field name',
    editField: mockEditField,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('labelPosition=Left: passes rulesets to FieldsetRulesetsBadge', () => {
    render(
      React.createElement(ExtraFieldFileTemplate, {
        ...baseProps,
        labelPosition: EFieldLabelPosition.Left,
      }),
    );

    const badgeMock = FieldsetRulesetsBadge as jest.Mock;
    expect(badgeMock).toHaveBeenCalledTimes(1);
    expect(badgeMock).toHaveBeenCalledWith(
      expect.objectContaining({ rulesets }),
      {},
    );
  });

  it('labelPosition=Top: passes rulesets to FieldsetRulesetsBadge', () => {
    render(
      React.createElement(ExtraFieldFileTemplate, {
        ...baseProps,
        labelPosition: EFieldLabelPosition.Top,
      }),
    );

    const badgeMock = FieldsetRulesetsBadge as jest.Mock;
    expect(badgeMock).toHaveBeenCalledTimes(1);
    expect(badgeMock).toHaveBeenCalledWith(
      expect.objectContaining({ rulesets }),
      {},
    );
  });

  it('labelPosition=Left: renders FieldLabel with labelPosition', () => {
    render(
      React.createElement(ExtraFieldFileTemplate, {
        ...baseProps,
        labelPosition: EFieldLabelPosition.Left,
      }),
    );

    const fieldLabelMock = FieldLabel as jest.Mock;
    expect(fieldLabelMock).toHaveBeenCalledTimes(1);
    expect(fieldLabelMock).toHaveBeenCalledWith(
      expect.objectContaining({ labelPosition: EFieldLabelPosition.Left }),
      {},
    );
  });
});

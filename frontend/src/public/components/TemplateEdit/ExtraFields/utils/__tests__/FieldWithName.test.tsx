import * as React from 'react';
import { render, screen, within } from '@testing-library/react';

import { FieldWithName } from '../FieldWithName';
import { FieldLabel } from '../FieldLabel';
import { Field } from '../../../../Field';
import { FieldsetRulesetsBadge } from '../../../../Fieldsets/FieldsetRulesetsBadge/FieldsetRulesetsBadge';
import { EExtraFieldMode } from '../../../../../types/template';
import { EFieldLabelPosition, EFieldRuleType } from '../../../../../types/fieldset';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';

jest.mock('../FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

jest.mock('../../../../Field', () => ({
  Field: jest.fn(() => null),
  EFieldTagName: {},
}));

jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

jest.mock('../../../../Fieldsets/FieldsetRulesetsBadge/FieldsetRulesetsBadge', () => ({
  FieldsetRulesetsBadge: jest.fn(() => React.createElement('span', { 'data-testid': 'rulesets-badge' })),
}));

describe('FieldWithName', () => {
  const mockHandleChangeName = jest.fn();
  const mockHandleChangeDescription = jest.fn();
  const mockValidate = jest.fn(() => '');

  const baseProps = {
    field: makeExtraField({ name: 'Test', description: 'Desc text', value: 'Val text' }),
    handleChangeName: mockHandleChangeName,
    handleChangeDescription: mockHandleChangeDescription,
    validate: mockValidate,
    isDisabled: false,
    labelPosition: EFieldLabelPosition.Top,
    mode: EExtraFieldMode.Kickoff,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('labelPosition → CSS class', () => {
    it('labelPosition=Top: container does NOT get label-left class', () => {
      render(React.createElement(FieldWithName, baseProps));

      const container = screen.getByLabelText('field-container');
      expect(container.className).not.toContain('label-left');
    });

    it('labelPosition=Left: container gets label-left class', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          labelPosition: EFieldLabelPosition.Left,
        }),
      );

      const container = screen.getByLabelText('field-container');
      expect(container.className).toContain('label-left');
    });
  });

  describe('labelClassName → FieldLabel', () => {
    it('passes labelClassName to FieldLabel when provided', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          labelClassName: 'custom-label-class',
        }),
      );

      const mock = FieldLabel as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(1);
      expect(mock).toHaveBeenCalledWith(expect.objectContaining({ className: 'custom-label-class' }), {});
    });

    it('does NOT pass className to FieldLabel when labelClassName is undefined', () => {
      render(React.createElement(FieldWithName, baseProps));

      const mock = FieldLabel as jest.Mock;
      expect(mock).toHaveBeenCalledTimes(1);
      const calledProps = mock.mock.calls[0][0];
      expect(calledProps).not.toHaveProperty('className');
    });
  });

  describe('description field value by mode', () => {
    it('uses description in Kickoff mode', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          mode: EExtraFieldMode.Kickoff,
        }),
      );

      const fieldMock = Field as jest.Mock;
      expect(fieldMock).toHaveBeenCalledTimes(1);
      expect(fieldMock).toHaveBeenCalledWith(expect.objectContaining({ value: 'Desc text' }), {});
    });

    it('uses value in ProcessRun mode', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          mode: EExtraFieldMode.ProcessRun,
        }),
      );

      const fieldMock = Field as jest.Mock;
      expect(fieldMock).toHaveBeenCalledTimes(1);
      expect(fieldMock).toHaveBeenCalledWith(expect.objectContaining({ value: 'Val text' }), {});
    });
  });

  describe('rulesets badge positioning by labelPosition', () => {
    const ruleset = {
      apiName: 'rs-1',
      name: 'Rule 1',
      type: EFieldRuleType.Validator,
      message: '',
      groupsOr: [],
      order: 0,
    };

    it('labelPosition=Left: renders badge in left label column', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          labelPosition: EFieldLabelPosition.Left,
          field: makeExtraField({
            name: 'Test',
            rulesets: [ruleset],
          }),
        }),
      );

      const labelCol = screen.getByLabelText('label-col');
      expect(within(labelCol).getByTestId('rulesets-badge')).toBeInTheDocument();

      const optionsContent = screen.getByLabelText('options-content');
      expect(within(optionsContent).queryByTestId('rulesets-badge')).not.toBeInTheDocument();
    });

    it('labelPosition=Top: renders badge in options content', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          labelPosition: EFieldLabelPosition.Top,
          field: makeExtraField({
            name: 'Test',
            rulesets: [ruleset],
          }),
        }),
      );

      expect(screen.queryByLabelText('label-col')).not.toBeInTheDocument();

      const optionsContent = screen.getByLabelText('options-content');
      expect(within(optionsContent).getByTestId('rulesets-badge')).toBeInTheDocument();
    });

    it('passes rulesets to FieldsetRulesetsBadge', () => {
      const rulesets = [ruleset];

      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          field: makeExtraField({
            name: 'Test',
            rulesets,
          }),
        }),
      );

      const badgeMock = FieldsetRulesetsBadge as jest.Mock;
      expect(badgeMock).toHaveBeenCalledTimes(1);
      expect(badgeMock).toHaveBeenCalledWith(
        expect.objectContaining({ rulesets }),
        {},
      );
    });

    it('empty rulesets: badge is called with empty array', () => {
      render(
        React.createElement(FieldWithName, {
          ...baseProps,
          field: makeExtraField({
            name: 'Test',
            rulesets: [],
          }),
        }),
      );

      const badgeMock = FieldsetRulesetsBadge as jest.Mock;
      expect(badgeMock).toHaveBeenCalledTimes(1);
      expect(badgeMock).toHaveBeenCalledWith(
        expect.objectContaining({ rulesets: [] }),
        {},
      );
    });
  });
});

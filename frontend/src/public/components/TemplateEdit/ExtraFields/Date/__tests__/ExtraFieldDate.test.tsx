/**
 * ExtraFieldDate — компонент поля даты.
 * Тестируем ТОЛЬКО ProcessRun label-left ветвления.
 * Kickoff делегирует через FieldWithName (покрыто отдельно).
 *
 * Контракт ProcessRun label-left:
 * - Left → FieldLabel с centered классом + date wrapper с _label-left
 * - Top → static name div, FieldLabel не рендерится
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldDate } from '../ExtraFieldDate';
import { FieldLabel } from '../../utils/FieldLabel';
import { IWorkflowExtraFieldProps } from '../../types';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';
import { EExtraFieldMode, EExtraFieldType } from '../../../../../types/template';
import { EFieldLabelPosition } from '../../../../../types/fieldset';

// --- Мок конфигурации ---

jest.mock('../../utils/FieldLabel', () => ({
  FieldLabel: jest.fn(() => null),
}));

jest.mock('../../utils/FieldWithName', () => {
  const React = require('react');
  return {
    FieldWithName: jest.fn(() => React.createElement('div', { 'data-testid': 'field-with-name' })),
  };
});

jest.mock('../../../../icons', () => ({
  DateIcon: () => null,
}));

jest.mock('../../utils/getFieldValidator', () => ({
  getFieldValidator: jest.fn(() => jest.fn(() => '')),
}));

jest.mock('../../utils/getInputNameBackground', () => ({
  getInputNameBackground: jest.fn(() => ''),
}));

jest.mock('../../../../UI/form/DatePicker', () => ({
  DatePickerCustom: jest.fn(() => null),
}));

jest.mock('../../../../../utils/dateTime', () => ({
  toDate: jest.fn(() => null),
  toTspDate: jest.fn(() => ''),
}));

// --- Тесты ---

describe('ExtraFieldDate', () => {
  const mockEditField = jest.fn();

  const baseProps: IWorkflowExtraFieldProps = {
    field: makeExtraField({ name: 'Due Date', type: EExtraFieldType.Date }),
    intl: intlMock,
    editField: mockEditField,
    mode: EExtraFieldMode.ProcessRun,
    isDisabled: false,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('label-left support', () => {
    // ProcessRun + Left → FieldLabel с centered
    it('ProcessRun + labelPosition=Left: renders FieldLabel with centered class', () => {
      render(<ExtraFieldDate {...baseProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
      expect(fieldLabelMock).toHaveBeenCalledWith(
        expect.objectContaining({
          className: expect.stringContaining('centered'),
        }),
        {},
      );
    });

    // ProcessRun + Top → static name div, no FieldLabel
    it('ProcessRun + labelPosition=Top: renders static name div, no FieldLabel', () => {
      render(<ExtraFieldDate {...baseProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('Due Date')).toBeInTheDocument();
    });
  });
});

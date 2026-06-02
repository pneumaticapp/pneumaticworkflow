/**
 * ExtraFieldFile — компонент файлового поля.
 * Тестируем ТОЛЬКО label-left ветвления (новый функционал).
 *
 * Контракт label-left:
 * - Kickoff + Left → FieldLabel, Kickoff + Top → inline textarea
 * - ProcessRun + Left → FieldLabel с aligned-start, ProcessRun + Top → static div
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { ExtraFieldFile } from '../ExtraFieldFile';
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

jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
  RemoveIcon: () => null,
}));

jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

jest.mock('../../../../../utils/uploadFiles', () => ({
  uploadFiles: jest.fn(),
}));

jest.mock('../../../../IntlMessages', () => ({
  IntlMessages: jest.fn(() => null),
}));

jest.mock('../../../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn(), success: jest.fn() },
}));

jest.mock('../ExtraFieldFilesGrid', () => ({
  ExtraFieldFilesGrid: jest.fn(() => null),
}));

jest.mock('../../../../UI/Buttons/Button', () => ({
  Button: jest.fn(() => null),
}));

jest.mock('../../../../../utils/logger', () => ({
  logger: { error: jest.fn(), info: jest.fn() },
}));

// --- Тесты ---

describe('ExtraFieldFile', () => {
  const mockEditField = jest.fn();

  // Правило 48: makeExtraField с минимальными overrides
  const baseProps: IWorkflowExtraFieldProps = {
    field: makeExtraField({ name: 'Attachment', type: EExtraFieldType.File }),
    intl: intlMock,
    editField: mockEditField,
    mode: EExtraFieldMode.Kickoff,
    isDisabled: false,
    accountId: 1,
    labelPosition: EFieldLabelPosition.Top,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('label-left support', () => {
    // Kickoff + Left → FieldLabel вызван
    it('Kickoff + labelPosition=Left: renders FieldLabel', () => {
      render(<ExtraFieldFile {...baseProps} labelPosition={EFieldLabelPosition.Left} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
    });

    // Kickoff + Top → FieldLabel не вызван
    it('Kickoff + labelPosition=Top: no FieldLabel', () => {
      render(<ExtraFieldFile {...baseProps} labelPosition={EFieldLabelPosition.Top} />);

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
    });

    // ProcessRun + Left → FieldLabel с aligned-start
    it('ProcessRun + labelPosition=Left: renders FieldLabel with aligned-start class', () => {
      render(
        <ExtraFieldFile
          {...baseProps}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Left}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).toHaveBeenCalledTimes(1);
      expect(fieldLabelMock).toHaveBeenCalledWith(
        expect.objectContaining({
          className: expect.stringContaining('aligned-start'),
        }),
        {},
      );
    });

    // ProcessRun + Top → static name div
    it('ProcessRun + labelPosition=Top: renders static name div, no FieldLabel', () => {
      render(
        <ExtraFieldFile
          {...baseProps}
          mode={EExtraFieldMode.ProcessRun}
          labelPosition={EFieldLabelPosition.Top}
        />,
      );

      const fieldLabelMock = FieldLabel as jest.Mock;
      expect(fieldLabelMock).not.toHaveBeenCalled();
      expect(screen.getByText('Attachment')).toBeInTheDocument();
    });
  });
});

import * as React from 'react';
import { render } from '@testing-library/react';

import { getVariables } from '../TaskForm/utils/getTaskVariables';
import {
  ITemplateEditVariablesSyncProps,
  TemplateEditVariablesSync,
} from '../TemplateEditVariablesSync';

jest.mock('../TaskForm/utils/getTaskVariables', () => ({
  getVariables: jest.fn(),
}));

const makeTemplate = (id: number | undefined) =>
  ({ id, kickoff: { fields: [], fieldsets: [] }, tasks: [] } as any);

describe('TemplateEditVariablesSync', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls loadTemplateVariablesSuccess when variable count changes', () => {
    const loadTemplateVariablesSuccess = jest.fn();
    const mockVariables = [{ apiName: 'v1' }, { apiName: 'v2' }] as any[];

    (getVariables as jest.Mock)
      .mockReturnValueOnce(mockVariables)
      .mockReturnValueOnce([{ apiName: 'v1' }]);

    render(
      React.createElement(TemplateEditVariablesSync, {
        template: makeTemplate(10),
        prevTemplate: makeTemplate(10),
        loadTemplateVariablesSuccess,
      } as ITemplateEditVariablesSyncProps),
    );

    expect(loadTemplateVariablesSuccess).toHaveBeenCalledTimes(1);
    expect(loadTemplateVariablesSuccess).toHaveBeenCalledWith({
      templateId: 10,
      variables: mockVariables,
    });

    expect(getVariables).toHaveBeenCalledTimes(2);
    expect(getVariables).toHaveBeenCalledWith(
      expect.objectContaining({ templateId: 10 }),
    );
  });

  it('does NOT call loadTemplateVariablesSuccess when variable count is unchanged', () => {
    const loadTemplateVariablesSuccess = jest.fn();
    const sameVars = [{ apiName: 'v1' }, { apiName: 'v2' }] as any[];

    (getVariables as jest.Mock)
      .mockReturnValueOnce(sameVars)
      .mockReturnValueOnce(sameVars);

    render(
      React.createElement(TemplateEditVariablesSync, {
        template: makeTemplate(10),
        prevTemplate: makeTemplate(10),
        loadTemplateVariablesSuccess,
      } as ITemplateEditVariablesSyncProps),
    );

    expect(loadTemplateVariablesSuccess).not.toHaveBeenCalled();
  });

  it('does NOT call loadTemplateVariablesSuccess when template.id is undefined', () => {
    const loadTemplateVariablesSuccess = jest.fn();

    (getVariables as jest.Mock)
      .mockReturnValueOnce([{ apiName: 'v1' }, { apiName: 'v2' }])
      .mockReturnValueOnce([{ apiName: 'v1' }]);

    render(
      React.createElement(TemplateEditVariablesSync, {
        template: makeTemplate(undefined),
        prevTemplate: makeTemplate(10),
        loadTemplateVariablesSuccess,
      } as ITemplateEditVariablesSyncProps),
    );

    expect(loadTemplateVariablesSuccess).not.toHaveBeenCalled();
  });
});

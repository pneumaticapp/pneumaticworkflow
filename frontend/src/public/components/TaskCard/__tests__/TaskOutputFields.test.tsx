import * as React from 'react';
import { render } from '@testing-library/react';

import { TaskOutputFields } from '../TaskOutputFields';
import { ETaskStatus } from '../../../redux/actions';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import {
  makeFieldsetRuntime,
  makeFieldRuleShowGroupAnd,
  makeFieldRuleGroupOr,
  makeFieldRuleSet,
} from '../../../__stubs__/fieldsets.factory';
import { EFieldRuleOperator, EFieldRuleType } from '../../../types/fieldset';
import { MergedOutputList } from '../../MergedOutputList';

jest.mock('../../MergedOutputList', () => ({
  MergedOutputList: jest.fn(() => React.createElement('div', { 'data-testid': 'merged-output-list' })),
}));

jest.mock('../../IntlMessages', () => ({
  IntlMessages: () => React.createElement('span', null, 'Help text'),
}));

describe('TaskOutputFields: dynamic field visibility by show rules', () => {
  const baseProps = {
    accountId: 1,
    editField: jest.fn(),
    editFieldsetField: jest.fn(),
    onUploadStateChange: jest.fn(),
    isDisabled: false,
    status: ETaskStatus.WaitingForAction,
    taskId: 10,
    fieldsetOutputValues: [],
    outputValues: [],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('hides task output field when its show ruleset condition is not met', () => {
    const triggerField = makeExtraField({ apiName: 'status-field', value: 'in_review' });
    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({
              field: 'status-field',
              operator: EFieldRuleOperator.Equal,
              value: 'approved',
            }),
          ],
        }),
      ],
    });
    const conditionalField = makeExtraField({
      apiName: 'resolution-notes',
      isHidden: true,
      rulesets: [showRuleset],
    });

    render(
      React.createElement(TaskOutputFields, {
        ...baseProps,
        outputValues: [triggerField, conditionalField],
      }),
    );

    const mergedMock = MergedOutputList as jest.Mock;
    expect(mergedMock).toHaveBeenCalledTimes(1);
    const lastCallProps = mergedMock.mock.calls[0][0];

    expect(lastCallProps.fields).toHaveLength(1);
    expect(lastCallProps.fields[0].apiName).toBe('status-field');
  });

  it('shows task output field when its show ruleset condition is met', () => {
    const triggerField = makeExtraField({ apiName: 'status-field', value: 'approved' });
    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({
              field: 'status-field',
              operator: EFieldRuleOperator.Equal,
              value: 'approved',
            }),
          ],
        }),
      ],
    });
    const conditionalField = makeExtraField({
      apiName: 'resolution-notes',
      isHidden: true,
      rulesets: [showRuleset],
    });

    render(
      React.createElement(TaskOutputFields, {
        ...baseProps,
        outputValues: [triggerField, conditionalField],
      }),
    );

    const mergedMock = MergedOutputList as jest.Mock;
    expect(mergedMock).toHaveBeenCalledTimes(1);
    const lastCallProps = mergedMock.mock.calls[0][0];

    expect(lastCallProps.fields).toHaveLength(2);
    expect(lastCallProps.fields[1].apiName).toBe('resolution-notes');
  });

  it('filters fields inside task fieldsets while preserving fieldset structure', () => {
    const triggerField = makeExtraField({ apiName: 'doc-type', value: 'passport' });
    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({
              field: 'doc-type',
              operator: EFieldRuleOperator.Equal,
              value: 'driving_license',
            }),
          ],
        }),
      ],
    });
    const fsField = makeExtraField({
      apiName: 'license-number',
      isHidden: true,
      rulesets: [showRuleset],
    });
    const fieldset = makeFieldsetRuntime({
      fields: [fsField],
    });

    render(
      React.createElement(TaskOutputFields, {
        ...baseProps,
        outputValues: [triggerField],
        fieldsetOutputValues: [fieldset],
      }),
    );

    const mergedMock = MergedOutputList as jest.Mock;
    expect(mergedMock).toHaveBeenCalledTimes(1);
    const lastCallProps = mergedMock.mock.calls[0][0];

    expect(lastCallProps.fields).toHaveLength(1);
    expect(lastCallProps.fieldsets).toHaveLength(1);
    expect(lastCallProps.fieldsets).toEqual([
      expect.objectContaining({
        fields: [],
      }),
    ]);
  });

  it('returns null and renders nothing when all fields are hidden by show rules', () => {
    const triggerField = makeExtraField({ apiName: 'status-field', value: 'in_review', isHidden: true });
    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [
            makeFieldRuleShowGroupAnd({
              field: 'status-field',
              operator: EFieldRuleOperator.Equal,
              value: 'approved',
            }),
          ],
        }),
      ],
    });
    const conditionalField = makeExtraField({
      apiName: 'resolution-notes',
      isHidden: true,
      rulesets: [showRuleset],
    });

    const { container } = render(
      React.createElement(TaskOutputFields, {
        ...baseProps,
        outputValues: [triggerField, conditionalField],
      }),
    );

    const mergedMock = MergedOutputList as jest.Mock;
    expect(mergedMock).not.toHaveBeenCalled();
    expect(container).toBeEmptyDOMElement();
  });
});

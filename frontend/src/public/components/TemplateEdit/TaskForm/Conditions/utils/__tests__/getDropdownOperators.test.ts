import { EConditionOperators } from '../../types';
import {
  conditionsByFieldTypeMap,
  EStartingType,
  getDropdownOperators,
  IDropdownOperator,
  labelByOperatorMap,
} from '../getDropdownOperators';
import { CONDITION_DISABLED_OPERATOR, OPERATORS_WITHOUT_VALUE } from '../shared';

describe('getDropdownOperators', () => {
  const mockMessages: Record<string, string> = {
    'templates.conditions.completed': 'Completed',
    'templates.conditions.skipped': 'Skipped',
    'templates.conditions.completed-or-skipped': 'Completed or Skipped',
    'templates.conditions.equal': 'Equals',
    'templates.conditions.not-equal': 'Not equals',
    'templates.conditions.exist': 'Filled in',
    'templates.conditions.not-exist': 'Not filled in',
    'templates.conditions.contain': 'Contains',
    'templates.conditions.not-contain': 'Not contains',
    'templates.conditions.more-than': 'More than',
    'templates.conditions.less-than': 'Less than',
  };

  describe('conditionsByFieldTypeMap', () => {
    it('includes Completed, Skipped and CompletedOrSkipped for EStartingType.Task', () => {
      const taskOperators = conditionsByFieldTypeMap[EStartingType.Task];

      expect(taskOperators).toEqual([
        EConditionOperators.Completed,
        EConditionOperators.Skipped,
        EConditionOperators.CompletedOrSkipped,
      ]);
    });

    it('includes only Completed for EStartingType.Kickoff', () => {
      const kickoffOperators = conditionsByFieldTypeMap[EStartingType.Kickoff];

      expect(kickoffOperators).toEqual([EConditionOperators.Completed]);
    });
  });

  describe('labelByOperatorMap', () => {
    it('maps Skipped to the correct intl key', () => {
      expect(labelByOperatorMap[EConditionOperators.Skipped]).toBe('templates.conditions.skipped');
    });

    it('maps CompletedOrSkipped to the correct intl key', () => {
      expect(labelByOperatorMap[EConditionOperators.CompletedOrSkipped]).toBe(
        'templates.conditions.completed-or-skipped',
      );
    });
  });

  describe('getDropdownOperators()', () => {
    it('returns 3 operators with correct labels for Task', () => {
      const result: IDropdownOperator[] = getDropdownOperators(EStartingType.Task, mockMessages);

      expect(result).toHaveLength(3);
      expect(result).toEqual([
        { operator: EConditionOperators.Completed, label: mockMessages['templates.conditions.completed'] },
        { operator: EConditionOperators.Skipped, label: mockMessages['templates.conditions.skipped'] },
        { operator: EConditionOperators.CompletedOrSkipped, label: mockMessages['templates.conditions.completed-or-skipped'] },
      ]);
    });

    it('returns only Completed for Kickoff', () => {
      const result: IDropdownOperator[] = getDropdownOperators(EStartingType.Kickoff, mockMessages);

      expect(result).toHaveLength(1);
      expect(result).toEqual([
        { operator: EConditionOperators.Completed, label: mockMessages['templates.conditions.completed'] },
      ]);
    });
  });
});

describe('OPERATORS_WITHOUT_VALUE', () => {
  it('contains all operators that do not require a value', () => {
    expect(OPERATORS_WITHOUT_VALUE).toEqual([
      EConditionOperators.Exist,
      EConditionOperators.NotExist,
      EConditionOperators.Completed,
      EConditionOperators.Skipped,
      EConditionOperators.CompletedOrSkipped,
    ]);
  });
});

describe('CONDITION_DISABLED_OPERATOR', () => {
  it('contains only Kickoff (Task is no longer disabled)', () => {
    expect(CONDITION_DISABLED_OPERATOR).toEqual([EStartingType.Kickoff]);
  });
});

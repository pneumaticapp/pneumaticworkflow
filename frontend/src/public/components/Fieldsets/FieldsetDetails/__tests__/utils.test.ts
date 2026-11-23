import { EFieldRuleType, EFieldLabelPosition } from '../../../../types/fieldset';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import {
  makeFieldRuleSet,
  makeFieldRuleGroupOr,
  makeFieldRuleShowGroupAnd,
  makeFieldsetCatalogItem,
  makeFieldsetRuleset,
  makeFieldsetRuleGroupOr,
  makeFieldsetRuleGroupAnd,
  makeFieldsetField,
} from '../../../../__stubs__/fieldsets.factory';
import { intlMock } from '../../../../__stubs__/intlMock';
import { NotificationManager } from '../../../UI/Notifications';
import { cloneFieldsetAction, updateFieldsetAction } from '../../../../redux/fieldsets/slice';
import { FIELDSET_RULES_MSG_RULE_REQUIRED } from '../../constants';
import { TLocalFieldsetState } from '../types';
import {
  getFieldsWithFilteredRulesets,
  initLocalFieldset,
  checkIsTitleError,
  getFieldsetChanges,
  saveFieldset,
  cloneFieldset,
} from '../utils';

jest.mock('../../../UI/Notifications', () => ({
  NotificationManager: {
    warning: jest.fn(),
  },
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  cloneFieldsetAction: jest.fn((payload) => ({ type: 'fieldsets/cloneFieldsetAction', payload })),
  updateFieldsetAction: jest.fn((payload) => ({ type: 'fieldsets/updateFieldsetAction', payload })),
}));

const makeLocalFieldsetState = (overrides: Partial<TLocalFieldsetState> = {}): TLocalFieldsetState => ({
  title: 'Филдсет',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  fields: [],
  rulesets: [],
  ...overrides,
});

describe('getFieldsWithFilteredRulesets', () => {
  it('removes show ruleset that references the deleted field', () => {
    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [
        makeFieldRuleSet({
          type: EFieldRuleType.Show,
          groupsOr: [
            makeFieldRuleGroupOr({
              groupsAnd: [makeFieldRuleShowGroupAnd({ field: 'field_b' })],
            }),
          ],
        }),
      ],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(0);
  });

  it('keeps show ruleset that references a different field', () => {
    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [
        makeFieldRuleSet({
          type: EFieldRuleType.Show,
          groupsOr: [
            makeFieldRuleGroupOr({
              groupsAnd: [makeFieldRuleShowGroupAnd({ field: 'field_c' })],
            }),
          ],
        }),
      ],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(1);
  });

  it('does not remove validator rulesets', () => {
    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [makeFieldRuleSet({ type: EFieldRuleType.Validator })],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(1);
  });

  it('returns field unchanged when it has no rulesets', () => {
    const fieldA = makeExtraField({ apiName: 'field_a' });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0]).toBe(fieldA);
  });

  it('removes show ruleset and keeps validator ruleset on the same field', () => {
    const showRuleset = makeFieldRuleSet({
      type: EFieldRuleType.Show,
      groupsOr: [
        makeFieldRuleGroupOr({
          groupsAnd: [makeFieldRuleShowGroupAnd({ field: 'field_b' })],
        }),
      ],
    });
    const validatorRuleset = makeFieldRuleSet({ type: EFieldRuleType.Validator });

    const fieldA = makeExtraField({
      apiName: 'field_a',
      rulesets: [showRuleset, validatorRuleset],
    });

    const result = getFieldsWithFilteredRulesets([fieldA], 'field_b');

    expect(result[0].rulesets).toHaveLength(1);
    expect(result[0].rulesets).toEqual([validatorRuleset]);
  });
});

describe('initLocalFieldset', () => {
  it('initializes local fieldset state with all fields', () => {
    const catalogItem = makeFieldsetCatalogItem({
      title: 'My Fieldset',
      description: 'Fieldset description',
      labelPosition: EFieldLabelPosition.Left,
      fields: [makeFieldsetField({ apiName: 'f1', name: 'Field 1' })],
      rulesets: [makeFieldsetRuleset({ apiName: 'rs1' })],
    });

    const state = initLocalFieldset(catalogItem);

    expect(state.title).toBe('My Fieldset');
    expect(state.description).toBe('Fieldset description');
    expect(state.labelPosition).toBe(EFieldLabelPosition.Left);
    expect(state.fields).toHaveLength(1);
    expect(state.rulesets).toHaveLength(1);
  });

  it('defaults description to empty string when missing', () => {
    const catalogItem = makeFieldsetCatalogItem({
      title: 'No description',
      description: '',
    });

    const state = initLocalFieldset(catalogItem);

    expect(state.description).toBe('');
  });
});

describe('checkIsTitleError', () => {
  it('returns true when title is empty and has changed', () => {
    const isError = checkIsTitleError('', true);

    expect(isError).toBe(true);
  });

  it('returns false when title is valid', () => {
    const isError = checkIsTitleError('Valid title', true);

    expect(isError).toBe(false);
  });

  it('returns false when title is empty but has not changed yet', () => {
    const isError = checkIsTitleError('', false);

    expect(isError).toBe(false);
  });
});

describe('getFieldsetChanges', () => {
  it('returns empty object when fieldset has not changed', () => {
    const initialFieldset = makeLocalFieldsetState({
      title: 'Title',
      description: 'Description',
      labelPosition: EFieldLabelPosition.Top,
      fields: [makeExtraField({ apiName: 'field-1', order: 0 })],
      rulesets: [makeFieldsetRuleset({ apiName: 'ruleset-1' })],
    });
    const localFieldset = { ...initialFieldset };

    const changes = getFieldsetChanges(initialFieldset, localFieldset);

    expect(changes).toEqual({});
  });

  it('returns only changed scalar properties', () => {
    const initialFieldset = makeLocalFieldsetState({
      title: 'Old Title',
      description: 'Same description',
      labelPosition: EFieldLabelPosition.Top,
    });
    const localFieldset = makeLocalFieldsetState({
      title: 'New Title',
      description: 'Same description',
      labelPosition: EFieldLabelPosition.Left,
    });

    const changes = getFieldsetChanges(initialFieldset, localFieldset);

    expect(changes).toEqual({
      title: 'New Title',
      labelPosition: EFieldLabelPosition.Left,
    });
  });

  it('returns empty description when description is cleared', () => {
    const initialFieldset = makeLocalFieldsetState({ description: 'Old description' });
    const localFieldset = makeLocalFieldsetState({ description: '' });

    const changes = getFieldsetChanges(initialFieldset, localFieldset);

    expect(changes).toEqual({ description: '' });
  });

  it('returns fields when two fields are swapped', () => {
    const initialFields = [
      makeExtraField({ apiName: 'field-1', order: 1 }),
      makeExtraField({ apiName: 'field-2', order: 0 }),
    ];
    const reorderedFields = [
      makeExtraField({ apiName: 'field-2', order: 1 }),
      makeExtraField({ apiName: 'field-1', order: 0 }),
    ];

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ fields: initialFields }),
      makeLocalFieldsetState({ fields: reorderedFields }),
    );

    expect(changes).toEqual({ fields: reorderedFields });
  });

  it('ignores fields array ordering and order offset shifts', () => {
    const initialFieldset = makeLocalFieldsetState({
      fields: [makeExtraField({ apiName: 'field-2', order: 1 }), makeExtraField({ apiName: 'field-1', order: 2 })],
    });
    const localFieldset = makeLocalFieldsetState({
      fields: [makeExtraField({ apiName: 'field-1', order: 1 }), makeExtraField({ apiName: 'field-2', order: 0 })],
    });

    const changes = getFieldsetChanges(initialFieldset, localFieldset);

    expect(changes).toEqual({});
  });

  it('ignores stripped undefined keys after moving field back', () => {
    const initialField = makeExtraField({
      apiName: 'field-1',
      order: 0,
      value: undefined,
    });
    const fieldAfterMoveBack = makeExtraField({
      apiName: 'field-1',
      order: 0,
    });
    delete fieldAfterMoveBack.value;

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ fields: [initialField] }),
      makeLocalFieldsetState({ fields: [fieldAfterMoveBack] }),
    );

    expect(changes).toEqual({});
  });

  it('ignores undefined vs empty array mismatches in field selections and rulesets', () => {
    const initialField = makeExtraField({
      apiName: 'field-1',
      order: 0,
      dataset: 5,
      selections: [],
      rulesets: undefined,
    });
    const revertedField = makeExtraField({
      apiName: 'field-1',
      order: 0,
      dataset: 5,
      selections: undefined,
      rulesets: [],
    });

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ fields: [initialField] }),
      makeLocalFieldsetState({ fields: [revertedField] }),
    );

    expect(changes).toEqual({});
  });

  it('ignores null vs empty message and regenerated groupOr apiName in field rulesets', () => {
    const firstRule = makeFieldRuleShowGroupAnd({ apiName: 'and-1', field: 'field-2', value: 'yes' });
    const secondRule = makeFieldRuleShowGroupAnd({ apiName: 'and-2', field: 'field-2', value: 'no' });

    const initialField = makeExtraField({
      apiName: 'field-1',
      rulesets: [
        makeFieldRuleSet({
          apiName: 'field-rs-1',
          message: null,
          groupsOr: [
            makeFieldRuleGroupOr({ apiName: 'or-original-1', groupsAnd: [firstRule] }),
            makeFieldRuleGroupOr({ apiName: 'or-original-2', groupsAnd: [secondRule] }),
          ],
        }),
      ],
    });
    const localField = makeExtraField({
      apiName: 'field-1',
      rulesets: [
        makeFieldRuleSet({
          apiName: 'field-rs-1',
          message: '',
          groupsOr: [
            makeFieldRuleGroupOr({ apiName: 'or-original-1', groupsAnd: [firstRule] }),
            makeFieldRuleGroupOr({ apiName: 'or-regenerated-2', groupsAnd: [secondRule] }),
          ],
        }),
      ],
    });

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ fields: [initialField] }),
      makeLocalFieldsetState({ fields: [localField] }),
    );

    expect(changes).toEqual({});
  });

  it('returns rulesets when a fieldset rule value changes', () => {
    const initialRulesets = [
      makeFieldsetRuleset({
        apiName: 'rs-1',
        fields: ['field-1'],
        groupsOr: [makeFieldsetRuleGroupOr({ groupsAnd: [makeFieldsetRuleGroupAnd({ value: '100' })] })],
      }),
    ];
    const updatedRulesets = [
      makeFieldsetRuleset({
        apiName: 'rs-1',
        fields: ['field-1'],
        groupsOr: [makeFieldsetRuleGroupOr({ groupsAnd: [makeFieldsetRuleGroupAnd({ value: '200' })] })],
      }),
    ];

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ rulesets: initialRulesets }),
      makeLocalFieldsetState({ rulesets: updatedRulesets }),
    );

    expect(changes).toEqual({ rulesets: updatedRulesets });
  });

  it('ignores reordered field list in fieldset sum ruleset', () => {
    const initialRulesets = [makeFieldsetRuleset({ apiName: 'rs-1', fields: ['field-1', 'field-2'] })];
    const localRulesets = [makeFieldsetRuleset({ apiName: 'rs-1', fields: ['field-2', 'field-1'] })];

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ rulesets: initialRulesets }),
      makeLocalFieldsetState({ rulesets: localRulesets }),
    );

    expect(changes).toEqual({});
  });

  it('ignores null vs empty message and regenerated groupOr apiName in fieldset rulesets', () => {
    const firstCondition = makeFieldsetRuleGroupAnd({ apiName: 'and-1', value: '10' });
    const secondCondition = makeFieldsetRuleGroupAnd({ apiName: 'and-2', value: '20' });

    const initialRulesets = [
      makeFieldsetRuleset({
        apiName: 'rs-1',
        order: 0,
        message: null,
        fields: ['field-1'],
        groupsOr: [
          makeFieldsetRuleGroupOr({ apiName: 'or-1', groupsAnd: [firstCondition] }),
          makeFieldsetRuleGroupOr({ apiName: 'or-2', groupsAnd: [secondCondition] }),
        ],
      }),
    ];
    const localRulesets = [
      makeFieldsetRuleset({
        apiName: 'rs-1',
        order: 0,
        message: '',
        fields: ['field-1'],
        groupsOr: [
          makeFieldsetRuleGroupOr({ apiName: 'or-1', groupsAnd: [firstCondition] }),
          makeFieldsetRuleGroupOr({ apiName: 'or-new', groupsAnd: [secondCondition] }),
        ],
      }),
    ];

    const changes = getFieldsetChanges(
      makeLocalFieldsetState({ rulesets: initialRulesets }),
      makeLocalFieldsetState({ rulesets: localRulesets }),
    );

    expect(changes).toEqual({});
  });
});

describe('saveFieldset', () => {
  const dispatchMock = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const EMPTY_FIELD_ERROR_MSG = formatMsg('validation.fieldset-title-empty');
  const RULE_REQUIRED_MSG = formatMsg(FIELDSET_RULES_MSG_RULE_REQUIRED);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does nothing when fieldset is null', () => {
    saveFieldset({
      fieldset: null,
      isChanged: true,
      localFieldset: makeLocalFieldsetState(),
      fieldsetChanges: { title: 'New' },
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
    });

    expect(NotificationManager.warning).not.toHaveBeenCalled();
    expect(dispatchMock).not.toHaveBeenCalled();
    expect(updateFieldsetAction).not.toHaveBeenCalled();
  });

  it('does nothing when there are no changes (isChanged=false)', () => {
    const fieldset = makeFieldsetCatalogItem({ id: 10 });

    saveFieldset({
      fieldset,
      isChanged: false,
      localFieldset: makeLocalFieldsetState(),
      fieldsetChanges: {},
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
    });

    expect(NotificationManager.warning).not.toHaveBeenCalled();
    expect(dispatchMock).not.toHaveBeenCalled();
    expect(updateFieldsetAction).not.toHaveBeenCalled();
  });

  it('shows warning and aborts save when title is empty', () => {
    const fieldset = makeFieldsetCatalogItem({ id: 10 });
    const localFieldset = makeLocalFieldsetState({ title: '' });

    saveFieldset({
      fieldset,
      isChanged: true,
      localFieldset,
      fieldsetChanges: { title: '' },
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
    });

    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith(
      expect.objectContaining({ message: EMPTY_FIELD_ERROR_MSG }),
    );
    expect(dispatchMock).not.toHaveBeenCalled();
    expect(updateFieldsetAction).not.toHaveBeenCalled();
  });

  it('shows warning and aborts save when modified ruleset has no rules', () => {
    const fieldset = makeFieldsetCatalogItem({ id: 10 });
    const localFieldset = makeLocalFieldsetState({ title: 'Fieldset' });
    const invalidRuleset = makeFieldsetRuleset({
      groupsOr: [{ apiName: 'go1', groupsAnd: [] }],
    });

    saveFieldset({
      fieldset,
      isChanged: true,
      localFieldset,
      fieldsetChanges: { rulesets: [invalidRuleset] },
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
    });

    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith(expect.objectContaining({ message: RULE_REQUIRED_MSG }));
    expect(dispatchMock).not.toHaveBeenCalled();
    expect(updateFieldsetAction).not.toHaveBeenCalled();
  });

  it('dispatches updateFieldsetAction with stripped field ids on valid data', () => {
    const fieldset = makeFieldsetCatalogItem({ id: 10 });
    const localFieldset = makeLocalFieldsetState({ title: 'Fieldset' });
    const fieldWithId = makeExtraField({
      id: 999,
      apiName: 'f1',
      name: 'Field 1',
    });
    const onSuccess = jest.fn();

    saveFieldset({
      fieldset,
      isChanged: true,
      localFieldset,
      fieldsetChanges: {
        title: 'Updated Name',
        fields: [fieldWithId],
      },
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
      onSuccess,
    });

    expect(NotificationManager.warning).not.toHaveBeenCalled();
    expect(updateFieldsetAction).toHaveBeenCalledTimes(1);
    expect(updateFieldsetAction).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 10,
        title: 'Updated Name',
        onSuccess,
        fields: [expect.not.objectContaining({ id: expect.anything() })],
      }),
    );
    expect(dispatchMock).toHaveBeenCalledTimes(1);
  });
});

describe('cloneFieldset', () => {
  const dispatchMock = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const CLONE_UNSAVED_WARNING = formatMsg('fieldsets.clone-unsaved-warning');

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows warning and does not dispatch cloneAction when there are unsaved changes', () => {
    cloneFieldset({
      fieldsetId: 10,
      isChanged: true,
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
    });

    expect(NotificationManager.warning).toHaveBeenCalledTimes(1);
    expect(NotificationManager.warning).toHaveBeenCalledWith(
      expect.objectContaining({ message: CLONE_UNSAVED_WARNING }),
    );
    expect(dispatchMock).not.toHaveBeenCalled();
    expect(cloneFieldsetAction).not.toHaveBeenCalled();
  });

  it('dispatches cloneFieldsetAction when there are no unsaved changes', () => {
    cloneFieldset({
      fieldsetId: 10,
      isChanged: false,
      dispatch: dispatchMock,
      formatMessage: intlMock.formatMessage,
    });

    expect(NotificationManager.warning).not.toHaveBeenCalled();
    expect(cloneFieldsetAction).toHaveBeenCalledTimes(1);
    expect(cloneFieldsetAction).toHaveBeenCalledWith({ id: 10 });
    expect(dispatchMock).toHaveBeenCalledTimes(1);
  });
});

import {
  EFieldRuleType,
  EFieldLabelPosition,
} from '../../../../types/fieldset';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import {
  makeFieldRuleSet,
  makeFieldRuleGroupOr,
  makeFieldRuleGroupAnd,
  makeFieldsetCatalogItem,
  makeFieldsetRuleset,
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
  updateFieldsetProperty,
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
          groupsOr: [makeFieldRuleGroupOr({
            groupsAnd: [makeFieldRuleGroupAnd({ field: 'field_b' })],
          })],
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
          groupsOr: [makeFieldRuleGroupOr({
            groupsAnd: [makeFieldRuleGroupAnd({ field: 'field_c' })],
          })],
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
      groupsOr: [makeFieldRuleGroupOr({
        groupsAnd: [makeFieldRuleGroupAnd({ field: 'field_b' })],
      })],
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

describe('updateFieldsetProperty', () => {
  it('calls both state setters with updated property value', () => {
    const setLocalFieldset = jest.fn();
    const setFieldsetChanges = jest.fn();

    updateFieldsetProperty('title', 'New Title', setLocalFieldset, setFieldsetChanges);

    expect(setLocalFieldset).toHaveBeenCalledTimes(1);
    expect(setFieldsetChanges).toHaveBeenCalledTimes(1);

    const localUpdater = setLocalFieldset.mock.calls[0][0];
    const changesUpdater = setFieldsetChanges.mock.calls[0][0];
    expect(localUpdater(makeLocalFieldsetState({ title: 'Old' }))).toEqual(
      expect.objectContaining({ title: 'New Title' }),
    );
    expect(changesUpdater({})).toEqual(
      expect.objectContaining({ title: 'New Title' }),
    );
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
    expect(NotificationManager.warning).toHaveBeenCalledWith(
      expect.objectContaining({ message: RULE_REQUIRED_MSG }),
    );
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
        fields: [
          expect.not.objectContaining({ id: expect.anything() }),
        ],
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

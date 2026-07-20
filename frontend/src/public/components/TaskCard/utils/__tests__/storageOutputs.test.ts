import {
  addOrUpdateStorageOutput,
  getOutputFromStorage,
  removeOutputFromLocalStorage,
  removeOutputsFromLocalStorage,
} from '../storageOutputs';
import { EExtraFieldType, IExtraField } from '../../../../types/template';

const OUTPUT_LOCALSTORAGE_KEY = 'tasks_outputs';

const createOutputField = (apiName: string): IExtraField => ({
  apiName,
  name: apiName,
  type: EExtraFieldType.Text,
  order: 1,
  userId: null,
  groupId: null,
  value: 'draft',
});

describe('storageOutputs', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('reads drafts saved with the legacy data property', () => {
    const legacyDraft = [createOutputField('legacy-field')];
    localStorage.setItem(OUTPUT_LOCALSTORAGE_KEY, JSON.stringify([{ taskId: 1, data: legacyDraft }]));

    expect(getOutputFromStorage(1)).toEqual(legacyDraft);
  });

  it('removes a single task output draft', () => {
    addOrUpdateStorageOutput(1, [createOutputField('field-a')]);
    addOrUpdateStorageOutput(2, [createOutputField('field-b')]);

    removeOutputFromLocalStorage(1);

    expect(getOutputFromStorage(1)).toBeUndefined();
    expect(getOutputFromStorage(2)).toEqual([createOutputField('field-b')]);
  });

  it('removes multiple task output drafts at once', () => {
    addOrUpdateStorageOutput(1, [createOutputField('field-a')]);
    addOrUpdateStorageOutput(2, [createOutputField('field-b')]);
    addOrUpdateStorageOutput(3, [createOutputField('field-c')]);

    removeOutputsFromLocalStorage([1, 3]);

    expect(getOutputFromStorage(1)).toBeUndefined();
    expect(getOutputFromStorage(2)).toEqual([createOutputField('field-b')]);
    expect(getOutputFromStorage(3)).toBeUndefined();
  });

  it('does nothing when removing from empty storage', () => {
    expect(() => removeOutputsFromLocalStorage([1, 2])).not.toThrow();
    expect(localStorage.getItem(OUTPUT_LOCALSTORAGE_KEY)).toBeNull();
  });
});

import {
  addOrUpdateStorageOutput,
  getOutputFromStorage,
  removeOutputFromLocalStorage,
  removeOutputsFromLocalStorage,
  outputStorage,
  fieldsetsStorage,
} from '../storageOutputs';
import { IExtraField } from '../../../../types/template';
import { IFieldsetRuntime } from '../../../../types/fieldset';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../../__stubs__/fieldsets.factory';

const OUTPUT_STORAGE_KEY = 'tasks_outputs';
const FIELDSETS_STORAGE_KEY = 'tasks_fieldsets_outputs';

describe('storageOutputs', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('persists draft metadata with the stored output', () => {
    const outputs = [makeExtraField({ apiName: 'plain', value: 'draft' })];
    const metadata = {
      dateStarted: '2024-01-01',
      fieldFingerprints: { plain: 'server-fingerprint' },
    };

    outputStorage.save(1, outputs, metadata);

    expect(outputStorage.getEntry(1)).toEqual({ taskId: 1, data: outputs, metadata });
  });

  it('keeps outputStorage and fieldsetsStorage isolated from each other', () => {
    const outputs: IExtraField[] = [makeExtraField({ apiName: 'plain', name: 'Field plain', value: 'plain-value' })];
    const fieldsets: IFieldsetRuntime[] = [
      makeFieldsetRuntime({ apiNameBinding: 'fs-1', name: 'Fieldset fs-1', fields: [makeExtraField({ apiName: 'fs-field', name: 'Field fs-field', value: 'fs-value' })] }),
    ];

    expect(getOutputFromStorage(1)).toBeUndefined();

    addOrUpdateStorageOutput(1, outputs);
    fieldsetsStorage.save(1, fieldsets);

    expect(getOutputFromStorage(1)).toEqual(outputs);
    expect(fieldsetsStorage.get(1)).toEqual(fieldsets);

    removeOutputFromLocalStorage(1);
    expect(getOutputFromStorage(1)).toBeUndefined();
    expect(fieldsetsStorage.get(1)).toEqual(fieldsets);
  });

  it('get returns undefined for a non-existent taskId', () => {
    expect(fieldsetsStorage.get(999)).toBeUndefined();
    expect(outputStorage.get(999)).toBeUndefined();
  });

  it('remove deletes only the entry for the given taskId, leaving other tasks intact', () => {
    const fs1: IFieldsetRuntime[] = [makeFieldsetRuntime({ apiNameBinding: 'fs-1', name: 'Fieldset fs-1', fields: [makeExtraField({ apiName: 'a', name: 'Field a', value: 'task-1-value' })] })];
    const fs2: IFieldsetRuntime[] = [makeFieldsetRuntime({ apiNameBinding: 'fs-2', name: 'Fieldset fs-2', fields: [makeExtraField({ apiName: 'b', name: 'Field b', value: 'task-2-value' })] })];

    fieldsetsStorage.save(1, fs1);
    fieldsetsStorage.save(2, fs2);

    fieldsetsStorage.remove(1);

    expect(fieldsetsStorage.get(1)).toBeUndefined();
    expect(fieldsetsStorage.get(2)).toEqual(fs2);
  });

  it('reads drafts saved with the legacy output property', () => {
    const outputs = [makeExtraField({ apiName: 'legacy', value: 'draft' })];
    localStorage.setItem(OUTPUT_STORAGE_KEY, JSON.stringify([{ taskId: 1, output: outputs }]));

    expect(outputStorage.get(1)).toEqual(outputs);
  });

  it('removes multiple output drafts and clears empty storage', () => {
    outputStorage.save(1, [makeExtraField({ apiName: 'first' })]);
    outputStorage.save(2, [makeExtraField({ apiName: 'second' })]);

    outputStorage.removeMany([1, 2]);

    expect(outputStorage.get(1)).toBeUndefined();
    expect(outputStorage.get(2)).toBeUndefined();
    expect(localStorage.getItem(OUTPUT_STORAGE_KEY)).toBeNull();
  });

  it('does nothing when removing from empty storage', () => {
    expect(() => removeOutputsFromLocalStorage([1, 2])).not.toThrow();
    expect(localStorage.getItem(OUTPUT_STORAGE_KEY)).toBeNull();
  });

  describe('corrupted localStorage data', () => {
    it.each<string>([
      'not a json',
      '{"taskId":1,"data":[]}',
      'null',
    ])('get returns undefined for corrupted value %p and does not throw', (raw) => {
      localStorage.setItem(FIELDSETS_STORAGE_KEY, raw);
      localStorage.setItem(OUTPUT_STORAGE_KEY, raw);

      expect(() => fieldsetsStorage.get(1)).not.toThrow();
      expect(() => outputStorage.get(1)).not.toThrow();

      expect(fieldsetsStorage.get(1)).toBeUndefined();
      expect(outputStorage.get(1)).toBeUndefined();
    });
  });
});

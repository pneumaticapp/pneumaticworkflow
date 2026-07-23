import { outputStorage, fieldsetsStorage } from '../storageOutputs';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetRuntime } from '../../../../__stubs__/fieldsets.factory';
import { IExtraField } from '../../../../types/template';
import { IFieldsetRuntime } from '../../../../types/fieldset';

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

    outputStorage.save(1, outputs);
    fieldsetsStorage.save(1, fieldsets);

    expect(outputStorage.get(1)).toEqual(outputs);
    expect(fieldsetsStorage.get(1)).toEqual(fieldsets);

    outputStorage.remove(1);

    expect(outputStorage.get(1)).toBeUndefined();
    expect(fieldsetsStorage.get(1)).toEqual(fieldsets);
  });

  it('save → get round-trip preserves the real fieldset structure 1-to-1', () => {
    const fieldsets: IFieldsetRuntime[] = [
      makeFieldsetRuntime({
        apiNameBinding: 'contacts',
        name: 'Contacts',
        description: 'Reachout details',
        order: 1,
        fields: [
          makeExtraField({ apiName: 'email', name: 'Field email', value: 'a@b.com' }),
          makeExtraField({ apiName: 'phone', name: 'Field phone', value: '+1', isRequired: true }),
        ],
      }),
      makeFieldsetRuntime({
        apiNameBinding: 'address',
        name: 'Fieldset address',
        order: 2,
        fields: [makeExtraField({ apiName: 'city', name: 'Field city', value: 'NY' })],
      }),
    ];

    fieldsetsStorage.save(7, fieldsets);

    expect(fieldsetsStorage.get(7)).toEqual(fieldsets);
  });

  it('subsequent save for the same taskId replaces the entry without duplicating', () => {
    fieldsetsStorage.save(1, [makeFieldsetRuntime({ apiNameBinding: 'fs', name: 'Fieldset fs', fields: [makeExtraField({ apiName: 'a', name: 'Field a', value: 'v1' })] })]);
    fieldsetsStorage.save(1, [makeFieldsetRuntime({ apiNameBinding: 'fs', name: 'Fieldset fs', fields: [makeExtraField({ apiName: 'a', name: 'Field a', value: 'v2' })] })]);

    const raw = localStorage.getItem(FIELDSETS_STORAGE_KEY);
    if (raw === null) {
      throw new Error('Expected localStorage to contain fieldsets entry');
    }
    const stored = JSON.parse(raw) as Array<{ taskId: number; data: IFieldsetRuntime[] }>;

    expect(stored).toHaveLength(1);
    expect(stored[0].taskId).toBe(1);
    expect(stored[0].data[0].fields[0].value).toBe('v2');
    expect(fieldsetsStorage.get(1)?.[0].fields[0].value).toBe('v2');
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

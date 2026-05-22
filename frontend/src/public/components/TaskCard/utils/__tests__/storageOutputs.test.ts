import { outputStorage, fieldsetsStorage } from '../storageOutputs';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../../types/template';

const OUTPUT_STORAGE_KEY = 'tasks_outputs';
const FIELDSETS_STORAGE_KEY = 'tasks_fieldsets_outputs';

const makeField = (apiName: string, overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName,
  name: `Field ${apiName}`,
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

const makeFieldset = (
  apiName: string,
  fields: IExtraField[],
  overrides: Partial<IFieldsetData> = {},
): IFieldsetData => ({
  id: 1,
  apiName,
  name: `Fieldset ${apiName}`,
  description: '',
  order: 0,
  fields,
  ...overrides,
});

describe('storageOutputs', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('keeps outputStorage and fieldsetsStorage isolated from each other', () => {
    const outputs: IExtraField[] = [makeField('plain', { value: 'plain-value' })];
    const fieldsets: IFieldsetData[] = [makeFieldset('fs-1', [makeField('fs-field', { value: 'fs-value' })])];

    outputStorage.save(1, outputs);
    fieldsetsStorage.save(1, fieldsets);

    expect(outputStorage.get(1)).toEqual(outputs);
    expect(fieldsetsStorage.get(1)).toEqual(fieldsets);

    outputStorage.remove(1);

    expect(outputStorage.get(1)).toBeUndefined();
    expect(fieldsetsStorage.get(1)).toEqual(fieldsets);
  });

  it('save → get round-trip preserves the real fieldset structure 1-to-1', () => {
    const fieldsets: IFieldsetData[] = [
      makeFieldset(
        'contacts',
        [
          makeField('email', { value: 'a@b.com', type: EExtraFieldType.String }),
          makeField('phone', { value: '+1', type: EExtraFieldType.String, isRequired: true }),
        ],
        { id: 42, name: 'Contacts', description: 'Reachout details', order: 1 },
      ),
      makeFieldset(
        'address',
        [makeField('city', { value: 'NY' })],
        { id: 43, order: 2 },
      ),
    ];

    fieldsetsStorage.save(7, fieldsets);

    expect(fieldsetsStorage.get(7)).toEqual(fieldsets);
  });

  it('subsequent save for the same taskId replaces the entry without duplicating', () => {
    fieldsetsStorage.save(1, [makeFieldset('fs', [makeField('a', { value: 'v1' })])]);
    fieldsetsStorage.save(1, [makeFieldset('fs', [makeField('a', { value: 'v2' })])]);

    const raw = localStorage.getItem(FIELDSETS_STORAGE_KEY);
    if (raw === null) {
      throw new Error('Expected localStorage to contain fieldsets entry');
    }
    const stored = JSON.parse(raw) as Array<{ taskId: number; data: IFieldsetData[] }>;

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
    const fs1: IFieldsetData[] = [makeFieldset('fs-1', [makeField('a', { value: 'task-1-value' })])];
    const fs2: IFieldsetData[] = [makeFieldset('fs-2', [makeField('b', { value: 'task-2-value' })])];

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

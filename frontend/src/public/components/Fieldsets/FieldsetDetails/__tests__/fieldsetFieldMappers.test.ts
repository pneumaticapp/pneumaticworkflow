
import { normalizeFieldForUI, normalizeFieldsForUI } from '../fieldsetFieldMappers';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { EExtraFieldType, IExtraField } from '../../../../types/template';

const makeField = (overrides: Partial<IExtraField> = {}) => makeExtraField({
  apiName: `f-${Math.random().toString(36).slice(2, 6)}`,
  ...overrides,
});

describe('fieldsetFieldMappers', () => {
  describe('normalizeFieldForUI', () => {
    it('sets default values for missing optional properties', () => {
      const input = {
        apiName: 'f-bare',
        name: 'Field',
        type: EExtraFieldType.String,
        order: 0,
      } as IExtraField;

      const result = normalizeFieldForUI(input);

      expect(result.description).toBe('');
      expect(result.isRequired).toBe(false);
      expect(result.isHidden).toBe(false);
      expect(result.dataset).toBeNull();
      expect(result.userId).toBeNull();
      expect(result.groupId).toBeNull();
    });

    it('preserves both truthy and falsy values without overwriting with defaults', () => {
      const input = makeField({
        description: 'desc',
        isRequired: true,
        isHidden: false,
        dataset: null,
        userId: 1,
        groupId: null,
      });

      const result = normalizeFieldForUI(input);

      expect(result.description).toBe('desc');
      expect(result.isRequired).toBe(true);
      expect(result.isHidden).toBe(false);
      expect(result.dataset).toBeNull();
      expect(result.userId).toBe(1);
      expect(result.groupId).toBeNull();
    });
  });

  describe('normalizeFieldsForUI', () => {
    it('normalizes an array of fields', () => {
      const fields = [
        makeField({ apiName: 'f1', description: undefined, isRequired: undefined }),
        makeField({ apiName: 'f2', description: undefined, isHidden: undefined }),
      ];

      const result = normalizeFieldsForUI(fields);

      expect(result).toHaveLength(2);
      expect(result[0].description).toBe('');
      expect(result[0].isRequired).toBe(false);
      expect(result[1].description).toBe('');
      expect(result[1].isHidden).toBe(false);
    });
  });
});

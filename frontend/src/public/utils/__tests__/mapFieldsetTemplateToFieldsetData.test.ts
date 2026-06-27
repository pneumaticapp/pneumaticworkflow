
import { mapFieldsetTemplateToFieldsetData } from '../mapFieldsetTemplateToFieldsetData';
import { EFieldLabelPosition } from '../../types/fieldset';
import { makeFieldsetCatalogItem, makeFieldsetField, makeFieldsetTemplateRule } from '../../__stubs__/fieldsets.factory';

describe('mapFieldsetTemplateToFieldsetData', () => {
  describe('camelCase keys (happy path)', () => {
    it('correctly maps all fields from camelCase format', () => {
      const template = makeFieldsetCatalogItem({
        fields: [makeFieldsetField({ apiName: 'f-1', name: 'Name', type: 'text', isRequired: true, isHidden: false, order: 3, default: 'hello' })],
        rules: [makeFieldsetTemplateRule({ apiName: 'r-1', type: 'show', value: 'x' })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.id).toBe(1);
      expect(result.apiName).toBe('fs-1');
      expect(result.name).toBe('Test Fieldset');
      expect(result.description).toBe('');
      expect(result.order).toBe(0);
      expect(result.labelPosition).toBe(EFieldLabelPosition.Top);
      expect(result.rulesCount).toBe(1);

      expect(result.fields).toHaveLength(1);
      expect(result.fields[0]).toEqual(expect.objectContaining({
        apiName: 'f-1',
        name: 'Name',
        type: 'text',
        isRequired: true,
        isHidden: false,
        order: 3,
        value: 'hello',
      }));
    });
  });

  describe('edge cases', () => {
    it('uses fallback apiName = fieldset-{id} when apiName is empty', () => {
      const template = makeFieldsetCatalogItem({ apiName: '', id: 42 });
      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.apiName).toBe('fieldset-42');
    });


  });

  describe('default to value mapping', () => {
    it('copies f.default into field value', () => {
      const template = makeFieldsetCatalogItem({
        fields: [makeFieldsetField({ default: 'prefilled' })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].value).toBe('prefilled');
    });

    it('sets empty string when default is not provided', () => {
      const template = makeFieldsetCatalogItem({
        fields: [makeFieldsetField({ default: undefined })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].value).toBe('');
    });
  });

  describe('labelPosition normalization', () => {
    it.each([
      [EFieldLabelPosition.Left, EFieldLabelPosition.Left],
      [EFieldLabelPosition.Top, EFieldLabelPosition.Top],
    ] as const)('labelPosition = %s results in %s', (input, expected) => {
      const template = makeFieldsetCatalogItem({
        labelPosition: input,
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.labelPosition).toBe(expected);
    });
  });

  describe('rulesCount', () => {
    it('counts rules from the array', () => {
      const template = makeFieldsetCatalogItem({
        rules: [
          makeFieldsetTemplateRule({ apiName: 'r-1', type: 'sum_equal', value: '100' }),
          makeFieldsetTemplateRule({ apiName: 'r-2', type: 'sum_equal', value: '50' }),
          makeFieldsetTemplateRule({ apiName: 'r-3', type: 'sum_equal', value: '25' }),
        ],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.rulesCount).toBe(3);
    });
  });

  describe('selections and dataset', () => {
    it('passes selections and dataset from field without modifications', () => {
      const selections = [{ apiName: 'opt-1', value: 'Option 1' }];
      const template = makeFieldsetCatalogItem({
        fields: [makeFieldsetField({ selections, dataset: 5 })],
      });

      const result = mapFieldsetTemplateToFieldsetData(template);

      expect(result.fields[0].selections).toBe(selections);
      expect(result.fields[0].dataset).toBe(5);
    });
  });
});

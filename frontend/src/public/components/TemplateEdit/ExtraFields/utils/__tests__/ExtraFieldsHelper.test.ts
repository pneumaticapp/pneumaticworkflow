/// <reference types="jest" />
import { ExtraFieldsHelper } from '../ExtraFieldsHelper';
import { EExtraFieldType, IExtraField } from '../../../../../types/template';

jest.mock('../../../../../utils/dateTime', () => ({
  getEndOfDayTsp: jest.fn((v: string) => `endOfDay(${v})`),
}));

const makeField = (overrides: Partial<IExtraField>): IExtraField => ({
  apiName: 'field-1',
  name: 'Test Field',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  ...overrides,
});

describe('ExtraFieldsHelper', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ───────────────────────────────────────────────────────────
  // normalizeFieldsValuesAsObject — called by completeTask API
  // ───────────────────────────────────────────────────────────
  describe('normalizeFieldsValuesAsObject', () => {
    describe('checkbox type', () => {
      it('wraps a single string value in an array (bug scenario)', () => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: 'New option' })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValuesAsObject();
        expect(result).toEqual({ 'field-1': ['New option'] });
      });

      it('keeps an array value as-is', () => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: ['opt1', 'opt2'] })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValuesAsObject();
        expect(result).toEqual({ 'field-1': ['opt1', 'opt2'] });
      });

      it.each([null, undefined, ''])('returns empty array for falsy value: %p', (falsy) => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: falsy as any })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValuesAsObject();
        expect(result).toEqual({ 'field-1': [] });
      });

      it('keeps an empty array as empty array', () => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: [] })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValuesAsObject();
        expect(result).toEqual({ 'field-1': [] });
      });
    });

    it('skips fields without apiName', () => {
      const fields = [makeField({ apiName: '', type: EExtraFieldType.Checkbox, value: 'opt' })];
      const result = new ExtraFieldsHelper(fields).normalizeFieldsValuesAsObject();
      expect(result).toEqual({});
    });

    it('normalizes multiple fields of different types', () => {
      const fields = [
        makeField({ apiName: 'cb-1', type: EExtraFieldType.Checkbox, value: 'New option' }),
        makeField({ apiName: 'url-1', type: EExtraFieldType.Url, value: 'http://a.com/b c' }),
        makeField({ apiName: 'txt-1', type: EExtraFieldType.Text, value: 'hello' }),
      ];
      const result = new ExtraFieldsHelper(fields).normalizeFieldsValuesAsObject();
      expect(result).toEqual({
        'cb-1': ['New option'],
        'url-1': 'http://a.com/b%20c',
        'txt-1': 'hello',
      });
    });
  });

  // ───────────────────────────────────────────────────────────
  // normalizeFieldsValues — used for kickoff
  // ───────────────────────────────────────────────────────────
  describe('normalizeFieldsValues', () => {
    describe('checkbox type', () => {
      it('wraps a string value in an array', () => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: 'opt1' })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValues();
        expect(result).toEqual([{ 'field-1': ['opt1'] }]);
      });

      it('keeps an array value as-is', () => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: ['a', 'b'] })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValues();
        expect(result).toEqual([{ 'field-1': ['a', 'b'] }]);
      });

      it.each([null, undefined, ''])('returns empty array for falsy value: %p', (falsy) => {
        const fields = [makeField({ type: EExtraFieldType.Checkbox, value: falsy as any })];
        const result = new ExtraFieldsHelper(fields).normalizeFieldsValues();
        expect(result).toEqual([{ 'field-1': [] }]);
      });
    });
  });

  // ───────────────────────────────────────────────────────────
  // getFieldsWithValues — used when task card initializes output
  // ───────────────────────────────────────────────────────────
  describe('getFieldsWithValues', () => {
    it('returns checkbox with default empty array when value is undefined', () => {
      const fields = [makeField({ type: EExtraFieldType.Checkbox, value: undefined })];
      const [first] = new ExtraFieldsHelper(fields).getFieldsWithValues();
      expect(first.value).toEqual([]);
    });

    it('returns checkbox with provided array value', () => {
      const fields = [makeField({ type: EExtraFieldType.Checkbox, value: ['opt1'] })];
      const [first] = new ExtraFieldsHelper(fields).getFieldsWithValues();
      expect(first.value).toEqual(['opt1']);
    });

    it('prefers storage value over initial value', () => {
      const fields = [makeField({ type: EExtraFieldType.Checkbox, value: undefined })];
      const storageOutput = [makeField({ type: EExtraFieldType.Checkbox, value: ['stored-opt'] })];
      const [first] = new ExtraFieldsHelper(fields, storageOutput).getFieldsWithValues();
      expect(first.value).toEqual(['stored-opt']);
    });

    it('passes through string value from backend (normalization happens later)', () => {
      const fields = [makeField({ type: EExtraFieldType.Checkbox, value: 'New option' })];
      const [first] = new ExtraFieldsHelper(fields).getFieldsWithValues();
      expect(first.value).toBe('New option');
    });
  });
});

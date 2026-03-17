import {
  createUUID,
  createUniqueId,
  createTaskApiName,
  createFieldApiName,
  createFieldSelectionApiName,
  createChecklistApiName,
  createChecklistSelectionApiName,
  createConditionApiName,
  createPerformerApiName,
  createConditionRuleApiName,
  createConditionPredicateApiName,
  createDueDateApiName,
  createOwnerApiName,
  createViewerApiName,
  createStarterApiName,
} from '../createId';

describe('createId utilities', () => {
  describe('createUUID', () => {
    it('generates a valid UUID format', () => {
      const uuid = createUUID();
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

      expect(uuid).toMatch(uuidRegex);
    });

    it('generates unique UUIDs', () => {
      const uuid1 = createUUID();
      const uuid2 = createUUID();

      expect(uuid1).not.toBe(uuid2);
    });
  });

  describe('createUniqueId', () => {
    it('replaces x with hex characters', () => {
      const id = createUniqueId('xxx');

      expect(id).toMatch(/^[0-9a-f]{3}$/);
    });

    it('replaces y with specific hex characters (8, 9, a, b)', () => {
      const ids = Array.from({ length: 100 }, () => createUniqueId('y'));
      const validYChars = ['8', '9', 'a', 'b'];

      ids.forEach((id) => {
        expect(validYChars).toContain(id);
      });
    });

    it('preserves non-pattern characters', () => {
      const id = createUniqueId('test-xxx');

      expect(id).toMatch(/^test-[0-9a-f]{3}$/);
    });
  });

  describe('createTaskApiName', () => {
    it('generates task api name with correct prefix', () => {
      const apiName = createTaskApiName();

      expect(apiName).toMatch(/^task-[0-9a-f]{6}$/);
    });
  });

  describe('createFieldApiName', () => {
    it('generates field api name with correct prefix', () => {
      const apiName = createFieldApiName();

      expect(apiName).toMatch(/^field-[0-9a-f]{6}$/);
    });
  });

  describe('createFieldSelectionApiName', () => {
    it('generates selection api name with correct prefix', () => {
      const apiName = createFieldSelectionApiName();

      expect(apiName).toMatch(/^selection-[0-9a-f]{6}$/);
    });
  });

  describe('createChecklistApiName', () => {
    it('generates checklist api name with correct prefix', () => {
      const apiName = createChecklistApiName();

      expect(apiName).toMatch(/^clist-[0-9a-f]{6}$/);
    });
  });

  describe('createChecklistSelectionApiName', () => {
    it('generates checklist item api name with correct prefix', () => {
      const apiName = createChecklistSelectionApiName();

      expect(apiName).toMatch(/^citem-[0-9a-f]{6}$/);
    });
  });

  describe('createConditionApiName', () => {
    it('generates condition api name with correct prefix', () => {
      const apiName = createConditionApiName();

      expect(apiName).toMatch(/^condition-[0-9a-f]{6}$/);
    });
  });

  describe('createPerformerApiName', () => {
    it('generates performer api name with correct prefix', () => {
      const apiName = createPerformerApiName();

      expect(apiName).toMatch(/^raw-performer-[0-9a-f]{6}$/);
    });
  });

  describe('createConditionRuleApiName', () => {
    it('generates rule api name with correct prefix', () => {
      const apiName = createConditionRuleApiName();

      expect(apiName).toMatch(/^rule-[0-9a-f]{6}$/);
    });
  });

  describe('createConditionPredicateApiName', () => {
    it('generates predicate api name with correct prefix', () => {
      const apiName = createConditionPredicateApiName();

      expect(apiName).toMatch(/^predicate-[0-9a-f]{6}$/);
    });
  });

  describe('createDueDateApiName', () => {
    it('generates due date api name with correct prefix', () => {
      const apiName = createDueDateApiName();

      expect(apiName).toMatch(/^due-date-[0-9a-f]{6}$/);
    });
  });

  describe('createOwnerApiName', () => {
    it('generates owner api name with correct prefix', () => {
      const apiName = createOwnerApiName();

      expect(apiName).toMatch(/^owner-[0-9a-f]{6}$/);
    });
  });

  describe('createViewerApiName', () => {
    it('generates viewer api name with correct prefix', () => {
      const apiName = createViewerApiName();

      expect(apiName).toMatch(/^viewer-[0-9a-f]{6}$/);
    });

    it('generates unique viewer api names', () => {
      const apiName1 = createViewerApiName();
      const apiName2 = createViewerApiName();

      expect(apiName1).not.toBe(apiName2);
    });
  });

  describe('createStarterApiName', () => {
    it('generates starter api name with correct prefix', () => {
      const apiName = createStarterApiName();

      expect(apiName).toMatch(/^starter-[0-9a-f]{6}$/);
    });

    it('generates unique starter api names', () => {
      const apiName1 = createStarterApiName();
      const apiName2 = createStarterApiName();

      expect(apiName1).not.toBe(apiName2);
    });
  });
});

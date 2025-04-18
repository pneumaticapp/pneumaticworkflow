/* eslint-disable no-bitwise */
export const createUUID = () => {
  const pattern = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx';

  return createUniqueId(pattern);
};

export const createUniqueId = (pattern: string) => {
  return pattern.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : ((r & 0x3) | 0x8);

    return v.toString(16);
  });
};

export const createTaskApiName = () => createUniqueId('task-xxxyxx');
export const createFieldApiName = () => createUniqueId('field-xxxyxx');
export const createFieldSelectionApiName = () => createUniqueId('selection-xxxyxx');
export const createChecklistApiName = () => createUniqueId('clist-xxxyxx');
export const createChecklistSelectionApiName = () => createUniqueId('citem-xxxyxx');
export const createConditionApiName = () => createUniqueId('condition-xxxyxx');
export const createPerformerApiName = () => createUniqueId('raw-performer-xxxyxx');
export const createConditionRuleApiName = () => createUniqueId('rule-xxxyxx');
export const createConditionPredicateApiName = () => createUniqueId('predicate-xxxyxx');
export const createDueDateApiName = () => createUniqueId('due-date-xxxyxx');
export const createOwnerApiName = () => createUniqueId('owner-xxxyxx');

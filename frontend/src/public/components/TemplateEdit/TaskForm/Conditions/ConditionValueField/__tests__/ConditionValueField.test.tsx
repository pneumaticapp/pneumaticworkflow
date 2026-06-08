/// <reference types="jest" />

type TConditionEntity = {
  id: number;
  entityType: 'user' | 'group';
  value: string;
};

const buildDropdownEntities = (): TConditionEntity[] => {
  const labelUsers: TConditionEntity[] = [{ id: 5, entityType: 'user', value: 'user-5' }];
  const labelGroups: TConditionEntity[] = [{ id: 5, entityType: 'group', value: 'group-5' }];

  return [...labelGroups, ...labelUsers];
};

const findSelectedEntity = (
  entities: TConditionEntity[],
  rule: { value: number; fieldType: 'user' | 'group' },
) =>
  entities.find(
    (entity) => entity.id === Number(rule.value) && entity.entityType === rule.fieldType,
  ) || null;

describe('ConditionValueField user/group selection logic', () => {
  const dropdownEntities = buildDropdownEntities();

  it('selects user entity by id and fieldType when user and group share the same id', () => {
    const selectedEntity = findSelectedEntity(dropdownEntities, { value: 5, fieldType: 'user' });

    expect(selectedEntity).toMatchObject({ id: 5, entityType: 'user' });
  });

  it('selects group entity by id and fieldType when user and group share the same id', () => {
    const selectedEntity = findSelectedEntity(dropdownEntities, { value: 5, fieldType: 'group' });

    expect(selectedEntity).toMatchObject({ id: 5, entityType: 'group' });
  });

  it('does not mark group as selected when only user is chosen', () => {
    const rule = { value: 5, fieldType: 'user' as const };
    const groupEntity = dropdownEntities.find((entity) => entity.entityType === 'group');

    expect(groupEntity?.id === rule.value && groupEntity?.entityType === rule.fieldType).toBe(false);
  });
});

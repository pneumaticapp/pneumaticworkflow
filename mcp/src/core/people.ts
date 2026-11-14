export interface PeopleDirectory {
  users: ReadonlyMap<number, string>;
  groups: ReadonlyMap<number, string>;
}

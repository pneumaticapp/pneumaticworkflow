export interface ITenant {
  id: number;
  tenantName: string;
  dateJoined: string;
}

export enum ETypeTenantModal {
  Create = 'create',
  EditName = 'edit-name',
}

export enum ETenantsSorting {
  NameAsc = 'name-asc',
  NameDesc = 'name-desc',
  DateAsc = 'date-asc',
  DateDesc = 'date-desc',
}

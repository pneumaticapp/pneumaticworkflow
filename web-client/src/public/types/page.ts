export interface IPagesStore {
  list: IPages;
}

export type IPages = IPage[];

export interface IPage {
  slug: string;
  title: string;
  description: string;
}

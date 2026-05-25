import fs from 'fs';
import path from 'path';
import { EExtraFieldType } from '../../src/public/types/template';

export const BACKEND_API_URL = process.env.PLAYWRIGHT_BACKEND_URL ?? 'http://localhost:8001';

export function getBearerToken(): string {
  const authFile = path.resolve(__dirname, '../.auth/user.json');
  const raw = fs.readFileSync(authFile, 'utf-8');
  const data = JSON.parse(raw) as { cookies: Array<{ name: string; value: string }> };
  const cookie = (data.cookies ?? []).find((c) => c.name === 'token');
  if (cookie) return cookie.value;
  throw new Error('getBearerToken: token not found in e2e/.auth/user.json');
}

export type TFieldType = EExtraFieldType;

export interface ICreateTemplateOptions {
  kickoffFields?: number | TFieldType[];
  taskFields?: number | TFieldType[];
  defaultFieldType?: TFieldType;
}

export interface IFieldInfo {
  apiName: string;
  name: string;
}

export interface ICreatedTemplate {
  templateId: number;
  kickoffFields: IFieldInfo[];
  taskFields: IFieldInfo[];
}

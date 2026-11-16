import type { ToolSelection } from './mcp/toolDef.js';
import type { PneumaticEndpoints } from './pneumatic/client.js';

export type Transport = 'stdio' | 'http';

export interface StdioConfig extends ToolSelection {
  transport: 'stdio';
  pneumatic: PneumaticEndpoints;
  apiKey: string;
}

export interface HttpConfig extends ToolSelection {
  transport: 'http';
  pneumatic: PneumaticEndpoints;
  host: string;
  port: number;
  publicUrl: URL;
  tokenSecret: string;
  replayFile: string;
  allowedRedirectHosts: string[];
  rateLimitPerMinute: number;
  trustProxy: boolean | number | string;
  metricsToken?: string;
}

export type Config = StdioConfig | HttpConfig;

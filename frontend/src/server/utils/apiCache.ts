import { CacheUtils } from './cacheUtils';

export const API_CACHE_EXPIRES = 60 * 60 * 12; // 12 hour

export const ApiCache = new CacheUtils(API_CACHE_EXPIRES);

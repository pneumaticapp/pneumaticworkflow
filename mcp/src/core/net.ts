export const LOOPBACK_HOSTS = ['localhost', '127.0.0.1', '[::1]'] as const;

export const isLoopbackHost = (hostname: string) => (LOOPBACK_HOSTS as readonly string[]).includes(hostname);

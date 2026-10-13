param(
    [string]$Image = 'pneumatic-mcp-service:test',
    [switch]$Build
)
$ErrorActionPreference = 'Stop'
$testsPath = $PSScriptRoot
$mcpPath = Split-Path -Parent $testsPath
$network = 'pneumatic-mcp-smoke-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
$containers = @()
$testSecret = 'docker-smoke-secret-0123456789-abcdef'

function Docker-Checked {
    param([string[]]$DockerArgs)
    & docker @DockerArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker smoke command failed with exit $LASTEXITCODE" }
}

try {
    if ($Build) { Docker-Checked @('build', '--tag', $Image, $mcpPath) }
    Docker-Checked @('network', 'create', '--internal', $network)
    $redisName = "$network-redis"
    $coreName = "$network-core"
    $mcpName = "$network-service"
    $customPortName = "$network-custom-port"
    $mount = "type=bind,source=$testsPath,target=/smoke,readonly"
    $containers += $redisName
    Docker-Checked @('run', '--detach', '--name', $redisName, '--network', $network,
        '--network-alias', 'redis', 'redis:7-alpine', 'redis-server', '--save', '', '--appendonly', 'no')
    $containers += $coreName
    Docker-Checked @('run', '--detach', '--name', $coreName, '--network', $network,
        '--network-alias', 'core', '--mount', $mount, '--env', "MCP_SERVICE_SECRET=$testSecret",
        '--entrypoint', '/app/.venv/bin/python', $Image, '/smoke/smoke_core.py')
    $containers += $mcpName
    Docker-Checked @('run', '--detach', '--name', $mcpName, '--network', $network,
        '--network-alias', 'mcp', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--env', 'MCP_ENABLED=yes', '--env', "MCP_SERVICE_SECRET=$testSecret",
        '--env', 'MCP_BACKEND_URL=http://core:8080/', '--env', 'MCP_FILE_SERVICE_URL=http://core:8080/',
        '--env', 'MCP_REDIS_URL=redis://redis:6379/5', $Image)
    Docker-Checked @('run', '--rm', '--network', $network, '--mount', $mount,
        '--env', "MCP_SERVICE_SECRET=$testSecret", '--entrypoint', '/app/.venv/bin/python',
        $Image, '/smoke/smoke_probe.py')
    $containers += $customPortName
    Docker-Checked @('run', '--detach', '--name', $customPortName, '--network', $network,
        '--network-alias', 'custom-port',
        '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--env', 'MCP_PORT=8123', '--env', 'MCP_ENABLED=yes',
        '--env', "MCP_SERVICE_SECRET=$testSecret", '--env', 'MCP_BACKEND_URL=http://core:8080/',
        '--env', 'MCP_FILE_SERVICE_URL=http://core:8080/', '--env', 'MCP_REDIS_URL=redis://redis:6379/5', $Image)
    Docker-Checked @('run', '--rm', '--network', $network, '--mount', $mount,
        '--env', "MCP_SERVICE_SECRET=$testSecret",
        '--entrypoint', '/app/.venv/bin/python', $Image, '/smoke/smoke_probe.py',
        '--endpoint', 'http://custom-port:8123/mcp', '--startup-only')
} catch {
    if ($mcpName) { & docker logs $mcpName }
    throw
} finally {
    foreach ($name in $containers) { & docker rm --force $name | Out-Null }
    & docker network rm $network | Out-Null
}

# Tools Prompt

## Available Tools
You have access to the following tools:

### File Operations
- `Read(path)` — read file contents
- `Write(path, content)` — create or overwrite a file
- `Edit(path, old, new)` — replace a string in a file
- `Glob(pattern)` — find files by pattern

### Search
- `Grep(pattern, path)` — search file contents by regex

### Execution
- `Bash(command)` — run shell commands

## Tool Usage Guidelines
1. Use dedicated tools (Read, Write, Edit) instead of Bash when available
2. Prefer parallel tool calls for independent operations
3. Validate paths exist before writing to nested directories
4. Quote paths with spaces in Bash commands

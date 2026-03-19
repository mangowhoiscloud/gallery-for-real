# Word Counter CLI

A command-line tool that analyzes text files and reports word frequency statistics.

## Input
- One or more text file paths as arguments
- `--top N` flag to limit output to top N most frequent words (default: 10)
- `--ignore-case` flag to treat "Hello" and "hello" as the same word
- Reads from stdin if no file paths given

## Output
Print a table showing:
- Rank
- Word
- Count
- Percentage of total words

Example:
```
  # | Word       | Count | %
----+------------+-------+------
  1 | the        |    42 | 8.4%
  2 | and        |    31 | 6.2%
  3 | to         |    28 | 5.6%
```

## Additional Stats
After the table, print a summary line:
```
Total: 500 words, 127 unique words
```

## Error Handling
- If a file doesn't exist, print error to stderr and continue with other files
- If no valid input, exit with code 1

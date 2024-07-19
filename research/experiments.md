# Experiments

Objective is to check assumptions on AI model details and development nuances at lowe cost and risk.

## Necessary model inputs
**Objective**: Define proper context input(content, format) for optimal model performance.

### JSON git history with diffs
**Overview**:
The model will be trained on the git history of the codebase. The git history will be represented as a JSON object.
Assumption is that model should use the content of the file to provide prompt with accurate context.

**Example**:
```json
{
  "commits": [
    {
      "author": "John Doe",
      "date": "2021-01-01T00:00:00Z",
      "message": "Initial commit",
      "diff": "diff --git a/file1 b/file1\nindex 0000000..1111111 100644\n--- a/file1\n+++ b/file1\n@@ -1,2 +1,2 @@\n-line1\n+line2\n line2\n line3\n"
    },
    {
      "author": "Jane Doe",
      "date": "2021-01-02T00:00:00Z",
      "message": "Add file2",
      "diff": "diff --git a/file2 b/file2\nnew file mode 100644\nindex 0000000..1111111\n--- /dev/null\n+++ b/file2\n@@ -0,0 +1,2 @@\n+line1\n+line2\n"
    }
  ]
}
```

## Prompts
**Objective**: Define the pattern of prompts that will be used to extract the necessary information from the codebase.

## Architecture
**Objective**: Find out the optimal way to:
- Provision the model
- Supply the model with context(schedule)
- Trigger runs
- Collect feedback(finetune)
- Implement multi tenancy(every user has its own model instance or share the same model instance)
- User defined configuration(manifest or config file vs inputs)
- Use vector store
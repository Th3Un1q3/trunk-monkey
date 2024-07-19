# Experiments

Objective is to check assumptions on AI model details and development nuances at lowe cost and risk.

## Necessary model inputs
**Objective**: Define proper context input(content, format) for optimal model performance.

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

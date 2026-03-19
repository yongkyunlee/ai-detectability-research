# [FEATURE] Include requestMetadata in Converse API calls(BedrockCompletion)

**Issue #4362** | State: closed | Created: 2026-02-04 | Updated: 2026-03-12
**Author:** mertsayar8
**Labels:** feature-request, no-issue-activity

### Feature Area

Core functionality

### Is your feature request related to a an existing bug? Please link it here.

Although `requestMetadata` field is supported by the [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_RequestSyntax), BedrockCompletion instance currently takes this field not into consideration and silently drops it before the Converse API calls.

### Describe the solution you'd like

`requestMetadata` is a crucial field for Bedrock, especially for Bedrock Model Invocation Logs. `BedrockCompletion` should be able to pass this field to the Converse API

### Describe alternatives you've considered

`request_metadata` will be taken as a parameter to the `BedrockCompletion` constructor, and will be included in the request body as `requestMetadata` along with other parameters  such as `additionalModelRequestFields` or `additionalModelResponseFieldPaths`.

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

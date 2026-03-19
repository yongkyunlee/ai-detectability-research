# [FEATURE]support for Bedrock system tool supports to utilize server side tool calling and as well response with grounding

**Issue #4363** | State: closed | Created: 2026-02-04 | Updated: 2026-03-12
**Author:** sktech730
**Labels:** feature-request, no-issue-activity

### Feature Area

Core functionality

### Is your feature request related to a an existing bug? Please link it here.

No.

### Describe the solution you'd like

This implementation adds support for AWS Bedrock system tools (specifically nova_grounding) to CrewAI, including automatic citation extraction from web-grounded responses.

**System Tool Flow (AWS Bedrock):**
1. LLM uses system tool internally
2. AWS Bedrock executes the tool
3. AWS Bedrock returns response with citations

Need to add the support to parse the response 

`{
  "output": {
    "message": {
      "content": [
        {
          "text": "Recent quantum computing developments include...",
          "citationsContent": [
            {
              "location": {
                "web": {
                  "url": "https://example.com/quantum-news",
                  "domain": "example.com"
                }
              }
            }
          ]
        }
      ]
    }
  }
}`

[Amazon Nova Web Grounding](https://aws.amazon.com/blogs/aws/build-more-accurate-ai-applications-with-amazon-nova-web-grounding/)
### Describe alternatives you've considered

N/A available as the Bedrock response includes new fields to response. those new fields would be ignored.flow continues without access to new fields

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

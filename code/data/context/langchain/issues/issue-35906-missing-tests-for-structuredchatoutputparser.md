# Missing tests for StructuredChatOutputParser

**Issue #35906** | State: open | Created: 2026-03-15 | Updated: 2026-03-15
**Author:** mokshagnachintha
**Labels:** external

There is an open TODO in \	est_structured_chat.py\ asking to add more tests. Specifically, the parser lacks tests for malformed JSON exceptions, list-responses from models like GPT-3.5, and missing action blocks. I am working on a PR to address this.

## Comments

**mokshagnachintha:**
@langchain-ai Please assign me to this issue so I can create a PR to resolve it. I have prepared comprehensive edge-case tests for the StructuredChatOutputParser. Ready to contribute!

**mokshagnachintha:**
## Assignment Request - Ready to Contribute

@langchain-ai maintainers, I'm ready to contribute comprehensive edge-case tests for StructuredChatOutputParser. 

### What I've Done:
✅ **3 production-ready tests** addressing the TODO:
- 	est_parse_malformed_json() - Invalid JSON exception handling
- 	est_parse_multiple_actions_in_list() - GPT-3.5-turbo list quirk handling
- 	est_parse_no_action_block() - Plain text fallback behavior

✅ **All tests passing** - 12/12 unit tests pass
✅ **Code quality** - Lint checks pass, no issues
✅ **Branch ready** - mokshagnachintha:add-edge-case-tests-final
✅ **49 insertions** - Comprehensive coverage

**Please assign me to this issue** so I can create a PR with Fixes #35906. I'm committed to completing this contribution and helping improve LangChain's test coverage!

Thank you!

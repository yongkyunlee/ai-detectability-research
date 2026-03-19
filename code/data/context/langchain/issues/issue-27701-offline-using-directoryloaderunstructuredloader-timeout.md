# Offline using DirectoryLoader/UnstructuredLoader timeout

**Issue #27701** | State: closed | Created: 2024-10-29 | Updated: 2026-03-06
**Author:** GanPeixin
**Labels:** bug

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

loader = DirectoryLoader("path/", glob="**/*.txt")
document = loader.load()

### Error Message and Stack Trace (if applicable)

_No response_

### Description

When I load a folder containing only 1 txt file into Document format offline using DirectoryLoader/UnstructuredLoader, it gets stuck at loader.load(). However, this issue does not occur when I switch to TextLoader.
What could be the situation? Does UnstructuredLoader load public URLs during its operation?

### System Info

offline 
python==3.12
langchain==0.3.4
langchain_community==0.3.3
langchain_unstructured==0.1.5

## Comments

**keenborder786:**
Hey, It's not hitting any Public URL. 

`DirectoryLoader` just loads the files as Documents using `UnstructuredFileLoader`. Unlike `UnstructuredAPIFileLoader`, it does not hit any public URL. What I would recommend is to use `show_progress` and `use_multithreading` to show and speed up the loading process respectively:
```python
loader = DirectoryLoader("path/", glob="**/*.txt", use_multithreading = True, show_progress = True)
```
Note that `TextLoader` loads one file as a single document while `DirectoryLoader` loads all the files as individual documents which match the `glob`. So if your case is loading a single file then you should use `TextLoader`. 

If you have many files in the `path/` Most likely `DirectoryLoader` might be taking too much time to load and match all of the files which you can see if you enable `show_progress`.

**garyfanhku:**
TL;DR, Langchain should be mindful of telemetry as discussed in https://github.com/langchain-ai/langchain/discussions/18382

`unstructured` package could be hitting `packages.unstructured.io:443` and you would need to set env variables as in https://github.com/Unstructured-IO/unstructured/issues/3459 to turn the it off. In offline environment, `scarf_analytics()` call seems to be blocking.

**dosubot[bot]:**
Hi, @GanPeixin. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- You reported a timeout issue with `DirectoryLoader` or `UnstructuredLoader` when loading a text file offline.
- User keenborder786 clarified that `DirectoryLoader` does not access public URLs and suggested using `show_progress` and `use_multithreading`.
- User garyfanhku identified that the `unstructured` package might be trying to connect to an external server and recommended setting environment variables to disable telemetry.

**Next Steps:**
- Please confirm if this issue is still relevant with the latest version of LangChain. If it is, feel free to comment to keep the discussion open.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!

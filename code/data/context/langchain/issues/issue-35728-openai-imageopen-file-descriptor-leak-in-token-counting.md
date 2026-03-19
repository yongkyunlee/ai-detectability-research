# openai: Image.open() file descriptor leak in token counting

**Issue #35728** | State: closed | Created: 2026-03-10 | Updated: 2026-03-12
**Author:** alvinttang
**Labels:** external

**Description**

`Image.open()` calls in the OpenAI token counting code don't use context managers, causing file descriptor leaks. There's even a comment on line 3696 about "close things (context managers)" that isn't followed.

**Affected file**
- `libs/partners/openai/langchain_openai/chat_models/base.py` — token counting code

**Suggested fix**
Wrap `Image.open()` calls with `with` context manager to ensure file descriptors are properly cleaned up.

## Comments

**mvanhorn:**
Submitted a fix in #35742. Both `Image.open()` calls in `_get_image_dimensions()` are now wrapped in `with` context managers so PIL Image handles (and their underlying file descriptors) are properly closed after reading dimensions.

**mvanhorn:**
I'd like to work on this issue. Could I be assigned?

**Financier-Nuri:**
## 技术分析

这是一个关于文件描述符泄漏的问题。感谢你发现这个问题！

### 问题确认

在的token计数代码中，确实需要使用上下文管理器来确保文件描述符被正确关闭。

### 建议修复方案

### 验证方法

可以通过以下方式验证修复效果：

### 相关最佳实践

-  文档明确建议使用上下文管理器
- Python 3.10+ 可以使用来标记不应修改的常量

---

*Unum AI 技术团队*

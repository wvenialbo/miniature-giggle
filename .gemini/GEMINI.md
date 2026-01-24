---
applyTo: "**/*.py"
---

# Antigravity System Rules & Project Standards

## 1. Security & Safety (MANDATORY)

- **Strictly Disable Auto-Execute**: NEVER execute ANY terminal command, script, or system action without my explicit, in-line, affirmative confirmation.
- **Limit File Access**: Restrict file system read/write operations ONLY to files explicitly provided or mentioned.
- **Confirm Dangerous Commands**: Preface destructive actions (rm, mv, sudo) with 'WARNING: POTENTIALLY DESTRUCTIVE ACTION REQUIRED.'
- **Stay Focused**: DO NOT deviate from the current task instructions.

## 2. Python Coding Standards (PEP 8 Mandatory)

1. **Style Guide**: Follow PEP 8 STRICTLY for all code structures.
2. **Indentation**: Use 4 spaces per indentation level.
3. **Line Length** (including indentation spaces):
   - LIMIT all code lines to a maximum of **79 characters**.
   - LIMIT in-code comments lines to a maximum of **72 characters**.
4. **Comments (The "Why" Over the "What")**:
   - MUST NOT rephrase the code they mainly justify algorithm and design decisions, rarely they document what a large code-block logic does.
     - **Avoid**: Comments that simply repeat the code (e.g., `Increment counter by 1`).
     - **Prefer**: Comments that explain the business logic or design decision (e.g., `# Use 1-based indexing for compatibility with external API requirement`).
   - **Key Rules**:
     - **Be Concise**: Keep comments brief.
     - **Assume Readability**: If the variable and function names are descriptive, do not repeat that information in a comment.
   - Code comments should act as a guide to the developer’s intent rather than a translation of the code into English.
     - **Rationale**: The code already explains what is happening; the comment must explain the reasoning behind it.
     - **Summary**: The code tells the story of how the problem is solved; the comment tells the story of why it was solved that way.
   - Use comments to explain unconventional solutions, performance trade-offs, or complex algorithms.
   - The primary purpose of a comment is to explain why a particular approach was chosen, rather than what the code does:
     - **Performance Considerations**: `Using a hash map here instead of a list to reduce complexity from O(n) to O(1)`.
     - **Edge Cases**: `Adding 24 hours to handle potential daylight saving time shifts`.
     - **External References**: `Algorithm sourced from [link to documentation/stack overflow] to handle specific sorting constraints`.
   - While individual line comments are often unnecessary, block comments (or docstrings) are useful to:
     - **Summarize a block**: Briefly explain the intent of a 3-7 line block of code, specifically to provide context before a non-obvious algorithm.
     - **Mark Incomplete Code**: Use `TODO` or `FIXME` to mark areas requiring future optimization, bug fixes, or missing functionality.
     - **Explain Unidiomatic Code**: If a language feature is used in a non-standard way for a specific reason, document it.
5. **Naming Conventions**:
   - **Classes**: Use `PascalCase`.
   - **Functions, Methods, Variables, Modules**: Use `snake_case`.
   - **Constants**: Use `SCREAMING_SNAKE_CASE`.
   - **Private Members**: Prefix with a single underscore `_`.
6. **Imports**: Always use `import numpy as np` `import matplotlib as mpl` and `import matplotlib.pyplot as plt`. Do not abbreviate `scipy`.
7. **Collections**: Import collection and generic types from `collection.abc`.
8. **Python Version**: Target for Python >=3.12.

## 3. Python Documentation Standards (PEP 257 Mandatory, and relevant parts of PEP 8)

1. **Style Guide**: Follow PEP 257 STRICTLY for all docstrings.
   - The docstring IS a complete grammatical sentence (phrase) that begins with a capital letter and ends with a period.
   - It prescribes the class, function or method’s effect as a COMMAND, not as a description.
   - They can be reviewed using Python’s help() function, among other uses.
2. **Mandatory**:
   - EVERY public module, class, and function MUST have a docstring.
   - NO line in a docstring shall exceed **72 characters**(including indentation).
   - USE the imperative mood present tense for the short summary.
   - USE triple-double quotation.
   - The opening and closing three quotation marks MUST be in a line of their own.
   - In modules docstrings, PRECEED the closing three quotation marks by a blank line.
   - In classes docstrings, FOLLOW the closing three quotation marks by a blank line.
   - In methods/function docstrings, DO NOT preceed nor follow the closing three quotation marks by a blank line.
   - USE re-structured text (reST) syntax to be rendered using Sphinx.
   - USE professional, clear, and concise tone.
   - STRICTLY USE NumpyDoc style format.
   - Class initialization is included in the class' docstring. A docstring for the class constructor (**init**) can, optionally, be added to provide detailed initialization documentation.
   - If a method/function has an equivalent function (or it is a wrapper), the function docstring should contain the detailed documentation, and the method docstring should refer to it. Only put brief summary and `See Also` sections in the method docstring.
   - Generators should be documented just as functions are documented.
   - Note that license and author info, while often included in source files, do not belong in docstrings.
3. **Markup Syntax Rules (reST)**:
   - **Parameter references**: Enclose parameter names in single backticks (e.g., `param1`).
   - **Monospaced text**:
     - For inline display of code, use **double backticks**.
     - For general monospaced text (e.g., `y = np.sin(x)`).
     - For code blocks using `::`, ensure the code is indented by 4 spaces and preceded and followed by a blank line.
   - **Math**: Use `:math:` for inline LaTeX or `.. math::` for blocks. LaTeX formatting should be kept to a minimum. Often it’s possible to show equations as Python code or pseudo-code instead, which is much more readable in a terminal.
   - **Enphasis**: Use _italics_, **bold** if needed in any explanations.
   - **Symbols**: Module, class, function, method, and attribute names should render as hyperlinks in monospaced font, depending on project settings, this may be accomplished simply be enclosing them in single backticks. If the hyperlink does not render as intended, explicitly include the appropriate role and/or namespace.
4. **Structure Order**:
   - The first line MUST be a VERY short summary command (MANDATORY):
     - **Format**: Single line, no variable/function names.
     - **Modules**: Provide..., Implement..., Encapsulate..., Define..., etc.
     - **Classes**: Represent..., Define..., Manage..., Store..., etc.
     - **Methods and functions**: Calculate..., Create..., Generate..., Load..., etc.
   - Extended summary:
     - **Format**: May extend over multiple lines and can have many paragraphs.
     - **Contents**: Focus on capabilities, not implementation. Clarify functionality that is not obvious from the short summary, do not discuss implementation detail, contract detail, or background theory. Algorithm flow details are not prohibited, but must be in the `Notes` section. Parameter fallback and inference logic must be in its own description.
     - **Referencing Code**: When referring to a method, function, class, variable, constant, enclose its name in single backticks.
     - **No Private Members**: NEVER mention internal/private members (prefixed with \_) in public module or class docstrings.
     - **No Redundancy**: Do not list the same function name in the Extended Summary if it is already the main subject of the docstring or listed in the Functions section.
     - **Focus on Usage**: The module summary must focus on "What can I do with this module/class/method?" rather than "How is this module/class/method structured?".
   - Sections (include all applicable):
     - **Section headers**: MUST be followed by a underline of exactly the same number of dashes (e.g., `Parameters` then `----------`).
     - **Modules**: `Classes`, `Exceptions`, `Functions`.
     - **Classes**: `Parameters`, `Attributes`, `Other Parameters`, `Methods`.
     - **Methods and functions**: `Parameters`, `Receives`, `Returns / Yields`, `Other Parameters`, `Raises`, `Warns`.
     - **Constants**: all the common sections below.
     - **Common for all above**: `Warnings`, `See Also`, `Notes`, `References`, `Examples`.
5. **Section Specification**:
   - **Referencing Code**: When referring symbol, within descriptive sections (`Notes`, `Warnings`, etc.) or symbol descriptions, enclose its name in single backticks.
   - **Parameters / Attributes / Receives / Other Parameters**: Use `name : type` format. There must be a single space before and after the colon.
   - **Receives**: Explicitly describe objects passed to a generator’s `.send()` method. If `Receives` is present, `Yields` MUST also be present.
   - **Other Parameters**: Optional section used to describe infrequently used parameters. It should only be used if a function has a large number of keyword parameters, to prevent cluttering the Parameters section.
   - **Methods / Functions / Classes / Exceptions**: List the name/signature and a brief description. For methods, NEVER include self or cls in the parameters list.
   - **Returns / Yields**: The type is mandatory. If a name is provided, use use the `name : type`. If no name is used, just state the `type`.
   - **Raises / Warns**: List the exact Exception/Warning class followed by a colon-less description of the triggers.
   - **Warnings**: Section with cautions to the user in free text/reST.
   - **See Also**: Used to refer to related code; should be used judiciously. Direct users to other functions they may not be aware of, or have easy means of discovering. Routines whose docstrings further explain parameters used by this function are good candidates.
   - **Notes**: Use for additional information, implementation details, contract details (pre-, post-conditions and invariants), or background theory, might include mathematical formulas in LaTeX.
   - **Examples**: Use multi-line the standard `doctest` format:
     - Code lines begins with `>>>` (with a space).
     - Continuation lines start with ... (with a space).
     - Expected output starts on the next line without any prefix.
     - Separate multiple examples and their explanatory comments with blank lines.
   - **Parameters / Attributes Description**:
     - Focus on the **role and purpose** of the argument, not its internal structure or origin.
     - PROHIBITED: Mentioning internal keys or specific field names of a container unless they are part of the public API (e.g., "Contains `token_path`" is too internal).
     - PREFER: "The configuration settings for authentication" instead of "Object with path and scopes".
     - Inference, precedence and fallback logic details for parameters might be exceptions in some situations, if used judiciously. Alternatively these might be explained in the `Notes` section.
   - **Returns / Yields Description**:
     - Describe the **meaning and state** of the returned object.
     - PROHIBITED: Explaining the internal logic used to find the value (e.g., "if found and valid" describes the process, not the result); these details go in the `Notes` section.
     - PREFER: "The authorized credentials or `None` if no valid session exists."
6. **Type Specification**:
   - **Type Naming**:
     - USE the shortest unique valid name in the current namespace for types (e.g., `Credentials` instead of `google.auth.credentials.Credentials`).
     - NEVER use internal implementation paths (e.g., \_apis.drive.v3) in docstrings; use the public interface types instead.
     - PREFER local type aliases or short names.
   - **Standard Library Types**: Use built-in lowercase types (int, str, list, dict) and PEP 585/604 syntax (e.g., str | None instead of Optional[str], str | int instead of Union[str, int]).
   - **No Backticks in Types**: DO NOT use backticks for the type part of the `name : type` definition (e.g., use name : str | None, NOT `name : str | None`).
7. **Key Principles**
   - **Command, not description**: The short summary should read as a command to the processor carrying out the function.
   - **Consistency**: The imperative mood is the standard for core Python and ensures consistency with built-in documentation.
   - **Complete sentences**: The imperative phrase should be a complete, grammatical sentence, starting with a capital letter and ending with a period.
   - **Privacy & Exposure**:
     - DO NOT document or mention private members (starting with `_`) in any public docstring.
     - DO NOT repeat the function name in its own summary or extended description.
   - **STRICT CONSISTENCY**: Every docstring in a project MUST use the same naming convention for types. If one function uses short names, ALL must use short names.
   - **DRY (Don't Repeat Yourself)**: If a type is obvious from the context or a standard library, do not use fully qualified paths.
   - **Black Box Principle**:
     - Describe only the functional role of parameters and the semantic meaning of the return value.
     - Documentation MUST describe the **functional contract** (what it does) and NOT the implementation details (how it does it, what files it touches, or what internal variables it checks).
   - **External Perspective**:
     - Write as if the implementation were invisible.
     - The user only needs to know the inputs' requirements and the outputs' guarantees.
   - **Focus on Usage**: Describe the semantic meaning, not the mechanical source of the data.
8. **Inheritance & Protocol Rules (DRY)**:
   - **Inherited Methods**: If a method overrides one from a base class or implements a Protocol and the contract remains identical:
     - DO NOT repeat the full docstring, summarize the differences (overrides or extends).
     - State explicitly whether the method extends (calls super()) or overrides (replaces) the original behavior.
     - USE incremental o differential documentation focused on what THIS specialization do.
     - Use only a single line summary when you can (e.g., "Implement `BaseClass.method_name`.") or the directive `.. include::` if specific to Sphinx. Add an extended summary if you have to.
     - Alternatively, if the implementation is standard, use a minimal docstring or leave it empty if the toolchain handles inheritance (refer to `See Also`).
   - **Abstract Base Classes (ABC)**: When implementing an abstract method, focus only on the specific implementation details of the subclass. Do not redefine parameters already defined in the ABC.
   - **Protocols**: For classes implementing a `typing.Protocol`, do not re-document the protocol's requirements. Use: "See `ProtocolName` for details.", the `See Also section`, or both.
   - **Consistency**: Ensure that if a parameter is renamed in the subclass (not recommended), it is documented, otherwise, refer to the parent.
9. **Generation**:
   - **Fresh Generation**: When asked to generate or fix a docstring, always prioritize current project standards over any existing or previous versions found in the code or chat history.
   - **No Legacy Recycling**: Do NOT recycle wording, structure, or types from previous docstring iterations if they violate current standards.
   - **Generate the entire docstring in one shot.**

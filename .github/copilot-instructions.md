---
applyTo: "**/*.py"
---

# GitHub Copilot System Rules & Project Standards

Unless stated as optional, all instructions are mandatory.

## 1. Security & Safety

1. **Strictly Disable Auto-Execute**:
   - NEVER execute ANY terminal command, script, or system action without my explicit, in-line, affirmative confirmation.
2. **Limit File Access**:
   - Restrict file system read/write operations ONLY to files explicitly provided or mentioned.
3. **Confirm Dangerous Commands**:
   - Preface destructive actions (rm, mv, sudo) with 'WARNING: POTENTIALLY DESTRUCTIVE ACTION REQUIRED.'

## 2. General Directives

These instructions apply to all the following sections in these `Project Standards`.

### 2.1. Tasking

1. **Stay Focused**:
   - DO NOT deviate from the current task instructions (e.g. do not write comments when writing documentation).
2. **Avoid Multi-Tasking**:
   - DO NOT perform more than one task at the same time (e.g. do not write docstrings for all functions if it was not requested).
   - DO NOT fix things if it was not explicitly requested.

### 2.2. Language

1. When writing documentation, comments, and error or warning messages:
   - USE a professional, clear, and concise tone.
   - STAY Pythonic when appropriate.
2. Adhere to UK grammar and spelling:
   - USE '-ise/-isation' endings (e.g. realise, organisation) or '-yse' (analyse).
   - USE British style and vocabulary (e.g. colour instead of color, analogue instead of analog).
   - USE "have got" rather than just "have" for possession.
   - USE "at the weekend" rather than "on the weekend".
   - USE "wrote to him" rather than "wrote him".
   - USE the Oxford comma generously for clarity.
   - PREFER plural verbs for collective nouns (e.g. "the committee are" vs "the committee is"); singular verbs are permitted depending on context.
3. Punctuation:
   - Use single quotation marks for quotes, with full stops outside the quotation mark if the quote is not a complete sentence.
   - Use double quotation marks for nested quotes.
   - No commas in thousands: 6580 instead of 6,580; avoid American-style gaps.

### 2.3. Indentation and Line Length

1. Use 4 spaces per indentation level.
2. LIMIT all code lines to a maximum of **79 characters**.
3. LIMIT in-code comment lines to a maximum of **72 characters**.
4. The above limits always include the indentation spaces.

## 3. Python Coding Standards

### 3.1. Python Version and Style Guide

1. Target Python >=3.12.
2. Follow PEP 8 STRICTLY for all code structures.

### 3.2. Naming Conventions

1. **Classes**: Use `PascalCase`.
2. **Functions, Methods, Variables, Modules**: Use `snake_case`.
3. **Constants**: Use `SCREAMING_SNAKE_CASE`.
4. **Private Members**: Prefix with a single underscore `_`.

### 3.3. Standard Library Types

1. USE PEP 585:
   - built-in lowercase types (e.g. `int`, `str`, `list`, `dict`).
   - complete generic types (e.g. `list[str]`, `tuple[int, ...]`).
2. USE PEP 604:
   - `X | Y` for union types instead of `Union[X, Y]`.
   - `X | None` for optional types instead of `Optional[str]`.
3. USE PEP 646:
   - `*args: Unpack[SomeTypeVarTuple]` for variable-length positional arguments.
4. USE PEP 692:
   - `**kwargs: Unpack[SomeTypedDict]` for variable-length keyword arguments.
5. USE PEP 695:
   - the `type` statement for type aliases (e.g. `type Vector = list[float]`).
   - clean generic syntax (e.g. `Box[T]` or `def func[T]...`).
6. NEVER type hint `self` or `cls`.

### 3.4. Imports

1. Use community-standard abbreviations (e.g. `import numpy as np`, `import pandas as pd`).
2. ALWAYS import abstract base classes from `collections.abc`; DO NOT use `typing` for these types.
3. ALWAYS import `Unpack`, `TypedDict`, and `TypeVarTuple` from the standard `typing` module; DO NOT use `typing_extensions`.

### 3.5. Error and Warning Messages

1. State errors as facts or conditions rather than conversational requests.
2. AVOID polite fillers like "Please". Stay Pythonic.
3. USE parameter or variable name, or name and value, if it will help to fix or debug the issue.
4. NEVER expose sensitive parameter or variable names, nor values (e.g. `client_secrets`), in an error or warning message.
5. ALWAYS use Pythonic style error messages.
6. Refer to Section 2.2 (Language) of these `Project Standards` for language style.

### 3.6. Comments (Prefer the "Why" Over the "What")

1. **Assume Readability**:
   - Code comments should act as a guide to the developer's intent rather than a translation of the code into English.
   - If variable and function names are descriptive, do not repeat that information in a comment.
   - **Rationale**: The code already explains what is happening; the comment must explain the reasoning behind it.
   - **Summary**: The code tells the story of how the problem is solved; the comment tells the story of why it was solved that way.
2. **Unconventional Solutions**:
   - Use comments to explain unconventional solutions, performance trade-offs, or complex algorithms.
   - The primary purpose of a comment is to explain why a particular approach was chosen, rather than what the code does.
3. **Large Code-block Logic**: While individual line comments are often unnecessary, block comments are useful to:
   - **Summarise a block**: Briefly explain the intent of a 3-7 line block of code, specifically to provide context before a non-obvious algorithm.
   - **Mark Incomplete Code**: Use `TODO` or `FIXME` to mark areas requiring future optimisation, bug fixes, or missing functionality.
   - **Explain Unidiomatic Code**: If a language feature is used in a non-standard way for a specific reason, document it.
4. **Examples**:
   - **Performance Considerations**: `Using a hash map here instead of a list to reduce complexity from O(n) to O(1)`.
   - **Edge Cases**: `Adding 24 hours to handle potential daylight saving time shifts`.
   - **External References**: `Algorithm sourced from [link to documentation/Stack Overflow] to handle specific sorting constraints`.
5. **Key Rules**:
   - BE CONCISE: Keep comments brief.
   - DO NOT rephrase the code: AVOID comments that simply repeat the code (e.g. `Increment counter by 1`).
   - EXPLAIN the business logic or design decision (e.g. `# Use 1-based indexing for compatibility with external API requirement`).
6. Refer to Section 2.2 (Language) of these `Project Standards` for language style.

## 4. Python Documentation Standards

### 4.1. Docstring Format and Style Guide

1. Follow PEP 257 STRICTLY (and relevant parts of PEP 8) for all docstring blocks.
2. STRICTLY USE `NumpyDoc` format for docstring structure and section organisation.
3. EVERY public module, class, method, and function MUST have a docstring.
4. Docstrings for private members are optional but follow the same rules.
5. Docstrings start and end with triple-double quotation marks.
6. Refer to Section 2.2 (Language) of these `Project Standards` for language style.

### 4.2. Markup Syntax Rules (reST)

1. USE reStructuredText (reST) syntax to be rendered using Sphinx.
2. Separate paragraphs with a blank line.
3. **Monospaced text**:
   - For general monospaced **text**, use single backticks (e.g. `y = np.sin(x)`).
   - For inline display of **code**, use double backticks (e.g. `load_file(filename)`).
   - Exception to the above rule: enclose parameter names in single backticks (e.g. `param1`).
   - For **code** blocks using `::`, ensure the code is indented by 4 spaces and is preceded and followed by a blank line.
4. **Math**:
   - Use `:math:` for inline LaTeX or `.. math::` for blocks.
   - Often it’s possible to show equations as Python code or pseudo-code instead, which is much more readable in a terminal.
   - LaTeX formatting should be kept to a minimum.
5. **Emphasis**:
   - Use _italics_, **bold** if needed in any explanations.
6. **Symbols**:
   - Module, class, function, method, and attribute names should render as hyperlinks in monospaced font.
   - Depending on project settings, this may be accomplished simply by enclosing them in single backticks.
   - If the hyperlink does not render as intended, explicitly include the appropriate role and/or namespace.
7. **Referencing Code**:
   - Rules 4.2.3 and 4.2.6 apply to symbol referencing within descriptive sections (e.g. `Extended Summary`, `Notes`, `Warnings`, etc.).
   - Rules 4.2.3 and 4.2.6 apply to symbol referencing within descriptive parts (e.g. description of `Parameters`, `Returns`, etc.).
   - For the declarative part of some sections (e.g. `Parameters`, `Returns`), use their own rules below.

### 4.3. Single-line Docstrings

- The opening and closing three quotation marks MUST NOT be followed by blank spaces.
- Single-line docstrings contain only the MANDATORY `Short Summary`.
- The entire docstring MUST fit within **72 characters**, including indentation and quotation marks.

### 4.4. Multi-line Docstring Blocks

1. The opening and closing three quotation marks MUST be on a line of their own.
2. The closing three quotation marks:
   - In modules and packages: are PRECEDED by a blank line.
   - In classes and exceptions: are FOLLOWED by a blank line.
   - In methods and functions: HAVE NO blank line around them.

### 4.5. Structure and Order

1. The first line is a single-line MANDATORY `Short Summary`:
   - It is FOLLOWED by a blank line in multi-line docstrings.
2. An optional `Extended Summary` follows the `Short Summary`:
   - It may extend over multiple lines.
   - It can have many paragraphs.
3. Component sections are placed below the summaries:
   - Include all applicable sections for the current entity (see below).

### 4.6. The Short Summary

1. **Command, not description**:
   - The short summary should read as a COMMAND to the processor carrying out the function, not as a description.
   - It prescribes the class, function, or method's effect in a phrase.
   - It can be reviewed using Python's `help()` function, among other uses.
2. **Consistency**:
   - The imperative mood is the standard for core Python and ensures consistency with built-in documentation.
   - It MUST NOT contain variable or function names.
3. **Complete sentences**:
   - It BEGINS with a verb USING the imperative mood present tense.
   - It STARTS with a capital letter and ENDS with a period.
   - It IS a complete grammatical sentence.
4. **Suggested Verbs**:
   - **For Modules or Packages**: Provide..., Implement..., Encapsulate..., Define..., etc. An encompassing or service action.
   - **For Classes or Exceptions**: Represent..., Define..., Manage..., Store..., etc. A collective action.
   - **For Methods or Functions**: Calculate..., Create..., Generate..., Load..., etc. An atomic action.

### 4.7. The Extended Summary

1. **Focus on Usage or Capabilities**:
   - MUST focus on "What can I do with this?" and "How can I do it?"
   - RATHER THAN "How is this structured?" or "How is it done?"
   - Black Box Principle: Write as if the implementation were invisible.
   - The user only needs to know the input requirements and the output guarantees.
   - Describe the semantic meaning, not the mechanical source of the data.
2. **Contents**:
   - Clarify functionality that is not obvious from the short summary.
   - For protocols, classes, and functions, describe the functional contract (what it does).
   - Do not discuss implementation details (how it does it, what files it touches, or what internal variables it checks); discuss them in the `Notes` section if needed.
   - Do not discuss background theory; discuss it in the `Notes` section.
   - Do not discuss algorithm flow, fallback, or inference logic; discuss them in the `Notes` section or in the `Parameters` description.
3. **Referencing Code**:
   - See Rules 4.2.3, 4.2.6, and 4.2.7 for referring to a method, function, class, variable, constant, or any symbol.
   - NEVER mention private members (prefixed with `_`) in any public member's docstrings.
   - DO NOT repeat the function, method, or class name in its own summary.
   - DO NOT mention the function or method name if it is already listed in the `Functions` or `Methods` section.

### 4.8. Sections

1. **Section headers**:
   - The section name BEGINS with a capital letter.
   - It MUST be followed by an underline of exactly the same number of dashes.
   - Example: `Parameters` then `----------`.
2. **Available Sections** (include all applicable):
   - **Packages**: `Contents`, `Subpackages`, `Modules`.
   - **Modules**: `Classes`, `Exceptions`, `Functions`.
   - **Classes, Protocols and Exceptions**: `Parameters`, `Attributes`, `Other Parameters`, `Methods`.
   - **Methods and Functions**: `Parameters`, `Receives`, `Returns / Yields`, `Other Parameters`, `Raises`, `Warns`.
   - **Constants**: all the common sections below.
   - **Common for all above**: `Warnings`, `See Also`, `Notes`, `References`, `Examples`.

### 4.9. Sections: Parameters / Attributes

1. **Declarative Part**:
   - USE `name : type` format.
   - There MUST be a single space before and after the colon.
   - DO NOT use backticks for the parameter name or type in the declaration.
   - For the parameter types, be as precise as possible. See Section 4.27.4 (Special Cases and Considerations) below.
   - USE `x : type, optional` for a keyword argument with a default value that would not be used.
   - USE `x : type, default=value` for a keyword argument with a default value that will be used.
   - USE `x : {'C', 'F', 'A'}` when a parameter can only assume one of a fixed set of values.
   - USE `x1, x2 : type` when two or more parameters have exactly the same type and description.
   - USE `*args : type` ONLY IF all positional arguments are STRICTLY of the same type.
   - USE `*args : Unpack[SomeTypeVarTuple]` IF a `TypeVarTuple` is defined for positional arguments; see Section 3.3.3 (Standard Library Types) for style compliance.
   - LEAVE `*args` without any type hint (including `: Any` or any generic annotation) in all other cases.
   - USE `**kwargs : type` ONLY IF all keyword arguments are STRICTLY of the same type.
   - USE `**kwargs : Unpack[SomeTypedDict]` IF a `TypedDict` is defined for SPECIFIC keys and their respective types; see Section 3.3.4 (Standard Library Types) for style compliance.
   - LEAVE `**kwargs` without any type hint (including `: Any`, `: dict`, or any generic annotation) in all other cases.
2. **Descriptive Part**:
   - Describe ONLY the functional **role and purpose** of the argument, not its internal structure or origin. PREFER "The configuration settings for authentication" to "Object with path and scopes".
   - NEVER expose sensitive parameters. PREFER "Path to authentication configuration file" to "Path to client secrets file".
   - Detail default values when their semantic meaning is not self-evident from the declarative part.
   - Discuss inference, precedence, and fallback logic judiciously. Alternatively, these might be explained in the `Notes` section.

### 4.10. Sections: Returns / Yields

1. **Declarative Part**:
   - USE `type` (mandatory) or `name : type` (optional) format.
   - See Section 4.9.1 for format specification.
2. **Descriptive Part**:
   - Describe ONLY the semantic **meaning and state** of the returned object/value.
   - Clarify special values if needed (often required with `bool` or signalling `None`).
   - NEVER expose sensitive values. PREFER: "The authorised credentials or `None` if no valid session exists."
   - DO NOT explain the internal logic used to find the value (e.g. "if found and valid" describes the process, not the result); these details might go in the `Notes` section.
3. When returning a multiple-valued object (`tuple`), write one declarative-descriptive block per value.

### 4.11. Sections: Receives

1. Explicitly describe objects passed to a generator’s `.send()` method.
2. If `Receives` is present, `Yields` MUST also be present.
3. It follows the structure of the `Parameters` section; see Section 4.9. (Sections: Parameters / Attributes).

### 4.12. Sections: Other Parameters

1. Optional section used to describe infrequently used parameters.
2. Use it only if a function has a large number of keyword parameters, to prevent cluttering the Parameters section.
3. It follows the structure of the `Parameters` section; see Section 4.9. (Sections: Parameters / Attributes).

### 4.13. Sections: Raises / Warns

1. **Declarative Part**:
   - USE `ExceptionType`, i.e. just the name of the exception/warning class.
2. **Descriptive Part**:
   - Detail under what conditions the exception/warning gets raised.
3. Write one declarative-descriptive block per exception/warning.
4. List ONLY exception/warning classes EXPLICITLY triggered WITHIN the method/function.
5. List ONLY errors that are non-obvious or have a large chance of getting raised.

### 4.14. Sections: Warnings

- A section with cautions to the user in free text/reST.

### 4.15. Sections: See Also

1. Should be used judiciously to refer to related code.
2. Direct users to:
   - Other functions they may not be aware of, or have easy means of discovering.
   - Routines whose docstrings further explain parameters used by this class/function; these are good candidates.
3. **Referencing Code**:
   - No prefix is needed when referring to symbols in the same sub-module.
   - USE partially qualified paths when referring to symbols from other sub-modules appropriately.
   - USE fully qualified paths when referring to an entirely different module.
4. **Structure**:
   - USE `name : Short description.`, in general.
   - USE `name` without a description, preferable if the functionality is clear from the symbol name.
   - USE one entry per line.
   - If the combination of the function name and the description creates a line that is too long, write the entry as two lines, with the function name and colon on the first line, and the description on the next line, indented 4 spaces.

### 4.16. Sections: Notes

1. Provides additional information about the code in free text/reST, possibly including:
   - A discussion of the algorithm.
   - Parameters fallback, or inference logic.
   - Background theory.
   - Contract details (pre-, post-conditions and invariants).
   - Implementation details (how it does it, what files it touches, or what internal variables it checks).
2. This section may include mathematical equations, written in LaTeX format; see Section 4.2 (Markup Syntax Rules).

### 4.17. Sections: References

References cited in the `Notes` section may be listed here, e.g. if you cited the article below using the text `[1]_`, include it as in the list as follows:

```rest
.. [1] Dunion, Jason P., Christopher D. Thorncroft, and Christopher S.
   Velden. "The tropical cyclone diurnal cycle of mature hurricanes."
   Monthly Weather Review 142.10 (2014): 3900-3919.
```

### 4.18. Sections: Examples

1. Use the standard `doctest` format:
   - Code lines begin with `>>>` (with a space).
   - Continuation lines start with ... (with a space).
   - Expected output starts on the next line without any prefix.
   - For tests with a result that is random or platform-dependent, mark the output by adding `#random`.
2. Separate multiple examples and their explanatory comments with blank lines.

### 4.19. Sections: Methods / Functions (Including Generators)

1. **Declarative Part**:
   - USE a shortened signature (name and parameters list): `function_name(arg1, arg2, ..., **kwargs)`.
   - DO NOT specify argument or return types.
   - NEVER include `self` or `cls` in the parameters list.
   - If the function signature extends over multiple lines, align continuation lines to the column following the opening parentheses.
2. **Descriptive Part**:
   - Write a brief description, usually a copy of the function's `Short Summary`.
3. Write one declarative-descriptive block per method/function/generator.

### 4.20. Sections: Classes / Exceptions (Including Protocols and Abstract Classes)

1. **Declarative Part**:
   - USE the class name: `MyClass`.
2. **Descriptive Part**:
   - Write a brief description, usually a copy of the class's `Short Summary`.
3. Write one declarative-descriptive block per class/exception/protocol.

### 4.21. Sections: Contents

- A section describing the package content in free text/reST; see Section 4.24 (Main Package Docstring) for a complete example.

### 4.22. Sections: Subpackages

- A section listing the subpackages of the current package in free text/reST; see Section 4.24 (Main Package Docstring) for a complete example.

### 4.23. Sections: Modules

- A section listing the modules of the current package in free text/reST.
- The structure is the same as the `Subpackages` section; see Section 4.22 (Sections: Subpackages) for more details.

### 4.24. Main Package Docstring

1. **Structure**:
   - For the main (parent) package, a title in the form "Package name: Brief summary or description".
   - An optional extended description.
   - The `Contents` and `Subpackages` sections.
2. **Example**:

```python
"""
SciPy: A scientific computing package for Python
================================================

Documentation is available in the docstrings and
online at https://docs.scipy.org/doc/scipy/.

Contents
--------

SciPy imports all the functions from the NumPy namespace, and in
addition provides:

Subpackages
-----------
Using any of these subpackages requires explicit import. For example,
``import scipy.cluster``.

::

 cluster                      --- Vector Quantization / Kmeans
 constants                    --- Physical and mathematical constants and units
 ...

Public API in the main SciPy namespace
--------------------------------------
::

 __version__       --- SciPy version string
 LowLevelCallable  --- Low-level callback function
 show_config       --- Show scipy build configuration
 test              --- Run scipy unittests

"""
```

### 4.25. Subpackages Docstring

- Similar to the main package docstring, but replaces the title with a normal `Short Summary`; see Section 4.24 (Main Package Docstring) for a complete example.

### 4.26. Other Entities' Docstrings

- They follow the general structure rules; see Sections 4.6 (The Short Summary) to 4.8 (Sections) and 4.27 (Special Cases) for details.

### 4.27. Special Cases and Considerations

1. **If a method/function has an equivalent function (e.g. a wrapper or specialisation)**:
   - Only put a brief summary and `See Also` sections in the main method/function docstring.
   - The main method/function docstring should contain the detailed documentation.
2. **Class initialisation**:
   - It is detailed in the class's docstring and in its `Parameters` section.
   - A docstring for the class constructor (`__init__`) can, optionally, be added to provide detailed initialisation documentation.
   - Non-trivial initialisation logic or important considerations within the file MUST be explained in the docstring.
3. **Generators**:
   - SHOULD be documented just as functions are documented.
4. **Type Specification**:
   - DO NOT use fully qualified paths if a type is obvious from the context.
   - PREFER local type aliases if available.
   - USE the shortest unique valid name in the current namespace for types (e.g. `Credentials` instead of `google.auth.credentials.Credentials`).
   - NEVER use internal implementation paths (e.g. `google._apis.drive.v3`) in docstrings; use the public interface types instead.
5. Note that licence and author info, while often included in source files, do not belong in docstrings.

### 4.28. Inheritance and Interface Implementation

1. If a method overrides one from a base class or implements a Protocol and the contract remains identical:
   - USE incremental or differential documentation focused on what THIS specialisation does.
   - DO NOT repeat the full docstring; summarise the differences (overrides or extends).
   - State explicitly whether the method extends (calls super()) or overrides (replaces) the original behaviour.
   - Use only a single line summary when you can (e.g. "Implement `BaseClass.method_name`.") or the directive `.. include::` if specific to Sphinx.
   - Add an extended summary if you have to.
   - Alternatively, if the implementation is standard, use a minimal docstring or leave it empty if the toolchain handles inheritance.
2. **Protocols and Abstract Base Classes**:
   - When implementing an abstract method, focus only on the specific implementation details of the subclass.
   - DO NOT redefine parameters already defined in the protocol/ABC.
   - For classes implementing a `typing.Protocol`, do not re-document the protocol's requirements.
   - USE "See `ProtocolName` for details.", the `See Also` section, or both.
3. **Consistency**:
   - Ensure that if a parameter is renamed in the subclass (not recommended), it is documented; otherwise, refer to the parent.

## 4.29. Wrap Up

1. **Generation**:
   - **Fresh Generation**: When asked to generate or fix a docstring, always prioritise current project standards over any existing or previous versions found in the code or chat history.
   - **No Legacy Recycling**: Do NOT recycle wording, structure, or types from previous docstring iterations if they violate current standards.
   - **Generate the entire docstring in one shot.**
2. **Keep everything Pythonic!**

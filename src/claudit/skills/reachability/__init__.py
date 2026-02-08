"""Code Reachability Analysis skill.

Find call paths between functions in large heterogeneous codebases
using GNU Global + static analysis with Pygments lexers.

Supported languages: C, Java, Python (one at a time, no cross-language).
"""

from claudit.skills.reachability.core import find_reachability

__all__ = ["find_reachability"]

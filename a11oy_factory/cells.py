"""Admitted and ROADMAP decision cells. Fail closed on anything else."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Honesty = Literal[
    "STRUCTURAL-ONLY",
    "ROADMAP",
    "CONJECTURE",
    "UNAVAILABLE",
]


@dataclass(frozen=True)
class Cell:
    id: str
    title: str
    organ: str
    honesty: Honesty
    admitted: bool
    bind: str
    note: str


LYTE = Cell(
    id="lyte",
    title="Lyte",
    organ="heart",
    honesty="STRUCTURAL-ONLY",
    admitted=True,
    bind="BIND_AS_A11OY_PACKAGE",
    note="The one admitted cell. Schema-checked bind into a11oy. Not a flagship.",
)

FRONTIERS: tuple[Cell, ...] = tuple(
    Cell(
        id=f"N{n}",
        title=f"Frontier N{n}",
        organ="nervous",
        honesty="ROADMAP",
        admitted=False,
        bind="BIND_AS_A11OY_PACKAGE",
        note="Named frontier. Compiler refuses admission until doctrine names it LIVE.",
    )
    for n in range(1, 9)
)

CELLS: dict[str, Cell] = {LYTE.id: LYTE, **{c.id: c for c in FRONTIERS}}
ADMITTED = frozenset(c.id for c in CELLS.values() if c.admitted)

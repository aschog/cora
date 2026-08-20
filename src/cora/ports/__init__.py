"""The seams: what cora needs from the outside world, one Protocol per thing.

A port states what the engine may ask for and what it may rely on getting back. Which
technology answers is `cora.app`'s decision, and the implementations live in
`cora.adapters` or in a suite's own fakes — a Protocol implementation inherits no
docstring, so what a port promises is written here or nowhere.
"""

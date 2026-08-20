"""The composition root: the only place that knows which technology fills which slot.

`build` is what a frontend calls, and `assemble` is the same app with the slots passed
in — which is what a test uses, and the reason nothing below this package imports an
adapter.
"""

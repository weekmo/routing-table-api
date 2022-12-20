"""
import polars as pl
@pl.api.register_expr_namespace("to_hex")
class Greetings:
    def __init__(self, expr: pl.Expr):
        self._expr = expr

    def get_hex(self) -> pl.Expr:
        return self._expr.cast(pl.UInt64)


df = pl.DataFrame(data=[20,14,28,50,10,234]).select(
    [
        pl.all().to_hex.get_hex().alias('hex')
    ]
)
"""

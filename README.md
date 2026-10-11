# indgroup

Format and parse integers and decimals in the Indian lakh and crore digit grouping

## Install

```
pip install indgroup
```

## Usage

The Indian system groups the last three digits, then the rest in pairs, so a
million reads as `10,00,000` and a crore as `1,00,00,000`.

```python
from decimal import Decimal
from indgroup import format_indian, parse_indian

format_indian(1234567)                 # "12,34,567"
format_indian(12596475)                # "1,25,96,475"
format_indian(-1234567)                # "-12,34,567"
format_indian(Decimal("1234567.89"))  # "12,34,567.89"
format_indian(1234567, separator=" ")  # "12 34 567"

parse_indian("12,34,567")              # 1234567 (int)
parse_indian("12,34,567.89")           # Decimal("1234567.89")
parse_indian("-1,234.5")               # Decimal("-1234.5")
```

Only the integer part is grouped; the fractional part is left untouched and
trailing zeros are preserved, so parsing is a faithful round trip. Values with
no fractional part parse back to `int`, decimals to `Decimal`. Western grouping
and any other malformed input raise `ValueError`.

## Why

Python's `locale` and `format` cannot produce Indian grouping portably, and the
`en_IN` locale is absent on most systems. The packages that mention lakh and
crore convert numbers to words (`lakh-crore-numbers` targets Nepali,
`currency-to-words`) or are tied to Django template filters
(`django-indian-numbers`); none is a plain, zero-dependency formatter and parser
for grouped numerals. Reach for this when you need to display or read back
amounts in the Indian convention with exact `Decimal` support.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/

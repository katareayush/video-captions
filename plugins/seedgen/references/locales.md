# Locale profiles

Compact reference for localizing generated test data. Match the requested locale, then generate values in that style. If a locale isn't here, infer equivalents from a real-world source for that region. Most faker libraries accept a locale code — prefer that when available (e.g. `faker` with `en_IN`, `en_GB`, `ja_JP`), and fall back to these hints.

| Locale | faker code | First names | Surnames | Phone format | Address style | Currency |
|--------|-----------|-------------|----------|--------------|---------------|----------|
| `indian` | `en_IN` | Aarav, Priya, Rohan, Ananya, Vikram, Diya | Sharma, Patel, Reddy, Iyer, Nair, Gupta | `+91 9XXXXXXXXX` (10 digits, starts 6-9) | Flat/House no., area, City, State, 6-digit PIN | INR (₹) |
| `us` | `en_US` | James, Emily, Michael, Olivia | Smith, Johnson, Williams, Brown | `+1 (XXX) XXX-XXXX` | Street, City, ST, 5-digit ZIP | USD ($) |
| `uk` | `en_GB` | Oliver, Amelia, Harry, Isla | Smith, Jones, Taylor, Brown | `+44 7XXX XXXXXX` | Street, Town, County, postcode (e.g. SW1A 1AA) | GBP (£) |
| `japanese` | `ja_JP` | Haruto, Yui, Sota, Aoi | Sato, Suzuki, Takahashi, Tanaka | `+81 90-XXXX-XXXX` | Prefecture, City, block — 7-digit postal | JPY (¥) |
| `german` | `de` | Lukas, Emma, Leon, Mia | Müller, Schmidt, Schneider, Fischer | `+49 1XX XXXXXXX` | Straße Nr., PLZ Stadt | EUR (€) |
| `french` | `fr` | Louis, Emma, Hugo, Léa | Martin, Bernard, Dubois, Thomas | `+33 6 XX XX XX XX` | No. rue, code postal Ville | EUR (€) |
| `brazilian` | `pt_BR` | Miguel, Alice, Arthur, Helena | Silva, Santos, Oliveira, Souza | `+55 (XX) 9XXXX-XXXX` | Rua, Bairro, Cidade-UF, CEP | BRL (R$) |
| `nigerian` | `en_NG` | Chidi, Ngozi, Emeka, Amara | Okafor, Adeyemi, Okoro, Balogun | `+234 8XX XXX XXXX` | Street, Area, City, State | NGN (₦) |

Guidance:
- Keep emails consistent with names (`priya.sharma@…`) and companies plausible for the region.
- Money fields: use the locale currency and realistic magnitudes.
- Mixed/no locale requested → default to `us`.
- A locale filter only changes *values*, never the schema — every constraint still holds.

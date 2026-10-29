simulators: ['iverilog', 'verilator']; flows: ['generic', 'ice40', 'ecp5', 'xilinx', 'liberty']

## Simulation (mismatches / samples)

| sample | iverilog | verilator |
| --- | --- | --- |
| example/candidate | pass | pass |
| haiku/01 | pass | pass |
| haiku/02 | pass | pass |
| haiku/03 | FAIL@compile | FAIL@compile |
| gpt-6-astra/01 | pass | pass |
| gpt-6-luna/01 | pass | pass |
| gpt-6.1-sol/01 | pass | pass |
| gpt-6.1-terra/01 | pass | pass |
| opus/01 | pass | pass |
| opus/02 | pass | pass |
| opus/03 | pass | pass |
| sonnet/01 | pass | pass |
| sonnet/02 | pass | pass |
| sonnet/03 | pass | pass |

## Reference metrics per flow

| flow | cells | depth | area |
| --- | --- | --- | --- |
| generic | 3063 | 31 | n/a |
| ice40 | 1600 | 25 | n/a |
| ecp5 | 2520 | 25 | n/a |
| xilinx | 2287 | 22 | n/a |
| liberty | 1991 | n/a | 14915.5552 |

## Candidate metrics per flow: cells / depth, reward (netlist re-sim)

| sample | generic | ice40 | ecp5 | xilinx | liberty |
| --- | --- | --- | --- | --- | --- |
| example/candidate | 3659 / d39, r=0.77 (ok) | 1562 / d27, r=0.97 (ok) | 4012 / d30, r=0.60 (ok) | 2188 / d26, r=0.93 (ok) | 2539 / 22137µm², r=0.86 (unverified) |
| haiku/01 | 4091 / d38, r=0.72 (ok) | 1654 / d26, r=0.96 (ok) | 1796 / d23, r=1.18 (ok) | 1458 / d23, r=1.16 (ok) | 2613 / 22223µm², r=0.84 (unverified) |
| haiku/02 | 3610 / d38, r=0.80 (ok) | 1552 / d26, r=0.99 (ok) | 3822 / d28, r=0.68 (ok) | 2050 / d26, r=0.96 (ok) | 2484 / 21661µm², r=0.88 (unverified) |
| haiku/03 | - | - | - | - | - |
| gpt-6-astra/01 | 3866 / d54, r=0.50 (ok) | 2128 / d36, r=0.61 (ok) | 1303 / d31, r=1.12 (ok) | 1982 / d33, r=0.82 (ok) | 2107 / 17699µm², r=0.97 (unverified) |
| gpt-6-luna/01 | 3768 / d54, r=0.51 (ok) | 2124 / d37, r=0.60 (ok) | 1709 / d32, r=1.02 (ok) | 1936 / d35, r=0.78 (ok) | 2001 / 16942µm², r=1.00 (unverified) |
| gpt-6.1-sol/01 | 3866 / d54, r=0.50 (ok) | 2130 / d36, r=0.61 (ok) | 1303 / d31, r=1.12 (ok) | 1982 / d33, r=0.82 (ok) | 2083 / 17628µm², r=0.98 (unverified) |
| gpt-6.1-terra/01 | 3558 / d37, r=0.82 (ok) | 1627 / d24, r=1.01 (ok) | 2461 / d22, r=1.07 (ok) | 2301 / d22, r=1.00 (ok) | 1988 / 14884µm², r=1.00 (unverified) |
| opus/01 | 3990 / d44, r=0.64 (ok) | 1636 / d27, r=0.95 (ok) | 2250 / d28, r=0.99 (ok) | 2228 / d26, r=0.92 (ok) | 2530 / 22373µm², r=0.86 (unverified) |
| opus/02 | 3673 / d41, r=0.74 (ok) | 1627 / d28, r=0.93 (ok) | 3982 / d30, r=0.61 (ok) | 1898 / d25, r=1.02 (ok) | 2458 / 21408µm², r=0.88 (unverified) |
| opus/03 | 3676 / d41, r=0.74 (ok) | 1609 / d28, r=0.94 (ok) | 4372 / d30, r=0.53 (ok) | 1911 / d25, r=1.01 (ok) | 2459 / 21270µm², r=0.88 (unverified) |
| sonnet/01 | 3625 / d38, r=0.80 (ok) | 1566 / d27, r=0.97 (ok) | 4039 / d30, r=0.60 (ok) | 2190 / d26, r=0.93 (ok) | 2540 / 22092µm², r=0.86 (unverified) |
| sonnet/02 | 3715 / d41, r=0.73 (ok) | 1605 / d27, r=0.96 (ok) | 3993 / d30, r=0.61 (ok) | 1925 / d25, r=1.01 (ok) | 2575 / 22074µm², r=0.85 (unverified) |
| sonnet/03 | 3609 / d38, r=0.80 (ok) | 1562 / d26, r=0.99 (ok) | 3798 / d28, r=0.69 (ok) | 2135 / d26, r=0.94 (ok) | 2462 / 21601µm², r=0.88 (unverified) |

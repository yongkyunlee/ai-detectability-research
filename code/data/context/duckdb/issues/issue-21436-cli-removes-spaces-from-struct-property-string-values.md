# CLI removes spaces from `STRUCT` property string values

**Issue #21436** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** tlinhart
**Labels:** reproduced

### What happens?

When querying data where a column is of `STRUCT` type with `VARCHAR` properties, under certain conditions the spaces (or maybe whitespaces in general) are removed from the property values in the output.

### To Reproduce

Prepare sample data:

```sql
CREATE TEMPORARY TABLE sample_data (
    data STRUCT(
        column1  VARCHAR,
        column2  VARCHAR,
        column3  VARCHAR,
        column4  VARCHAR,
        column5  VARCHAR,
        column6  VARCHAR,
        column7  VARCHAR,
        column8  VARCHAR,
        column9  VARCHAR,
        column10 VARCHAR,
        column11 VARCHAR,
        column12 VARCHAR,
        column13 VARCHAR,
        column14 VARCHAR,
        column15 VARCHAR,
        column16 VARCHAR,
        column17 VARCHAR,
        column18 VARCHAR,
        column19 VARCHAR,
        column20 VARCHAR
    )
);

INSERT INTO sample_data VALUES (
    {
        column1: 'apple river cloud hammer bright',
        column2: 'forest table ocean pencil green',
        column3: 'window marble stone quick silver',
        column4: 'garden bridge sunset flame candle',
        column5: 'rocket feather puzzle train bottle',
        column6: 'mountain crystal tiger basket lemon',
        column7: 'shadow lantern copper wheel breeze',
        column8: 'island violin anchor desert bloom',
        column9: 'thunder maple ribbon castle spark',
        column10: 'falcon mirror ladder pepper frost',
        column11: 'compass dragon velvet harbor arrow',
        column12: 'meadow trumpet coral engine blossom',
        column13: 'glacier pillow raven sketch amber',
        column14: 'beacon plume cedar tunnel oyster',
        column15: 'summit parrot mosaic ember walnut',
        column16: 'canyon dolphin quartz needle clover',
        column17: 'lantern pebble falcon orbit willow',
        column18: 'prism scarlet anchor marble dune',
        column19: 'temple cobalt raven timber flint',
        column20: 'atlas crimson hollow spruce pearl'
    }
);
```

Query the data:

```sql
SELECT * FROM sample_data;
```

The output is (on my terminal with 132x43 dimentions):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                               data                                                               │
│ struct(column1 varchar, column2 varchar, column3 varchar, column4 varchar, column5 varchar, column6 varchar, column7 varchar, co │
│ lumn8 varchar, column9 varchar, column10 varchar, column11 varchar, column12 varchar, column13 varchar, column14 varchar, column │
│              15 varchar, column16 varchar, column17 varchar, column18 varchar, column19 varchar, column20 varchar)               │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {                                                                                                                                │
│   'column1': applerivercloudhammerbright,                                                                                        │
│   'column2': foresttableoceanpencilgreen,                                                                                        │
│   'column3': windowmarblestonequicksilver,                                                                                       │
│   'column4': gardenbridgesunsetflamecandle,                                                                                      │
│   'column5': rocketfeatherpuzzletrainbottle,                                                                                     │
│   'column6': mountaincrystaltigerbasketlemon,                                                                                    │
│   'column7': shadowlanterncopperwheelbreeze,                                                                                     │
│   'column8': islandviolinanchordesertbloom,                                                                                      │
│   'column9': thundermapleribboncastlespark,                                                                                      │
│   'column10': falconmirrorladderpepperfrost,                                                                                     │
│   'column11': compassdragonvelvetharborarrow,                                                                                    │
│   'column12': meadowtrumpetcoralengineblossom,                                                                                   │
│   'column13': glacierpillowravensketchamber,                                                                                     │
│   'column14': beaconplumecedartunneloyster,                                                                                      │
│   'column15': summitparrotmosaicemberwalnut,                                                                                     │
│   'column16': canyondolphinquartzneedleclover,                                                                                   │
│   'column17': lanternpebblefalconorbitwillow,                                                                                    │
│   'column18': prismscarletanchormarbledune,                                                                                      │
│   'column19': templecobaltraventimberflint,                                                                                      │
│   'column20': atlascrimsonhollowsprucepearl                                                                                      │
│ }                                                                                                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

i.e. the spaces are missing in the string values.

Now add 4 more rows (the same values) and repeat the query. The output is:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                               data                                                               │
│ struct(column1 varchar, column2 varchar, column3 varchar, column4 varchar, column5 varchar, column6 varchar, column7 varchar, co │
│ lumn8 varchar, column9 varchar, column10 varchar, column11 varchar, column12 varchar, column13 varchar, column14 varchar, column │
│              15 varchar, column16 varchar, column17 varchar, column18 varchar, column19 varchar, column20 varchar)               │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {'column1': apple river cloud hammer bright, 'column2': forest table ocean pencil green, 'column3': window marble stone quick si │
│ lver, 'column4': garden bridge sunset flame candle, 'column5': rocket feather puzzle train bottle, 'column6': mountain crystal t │
│ iger basket lemon, 'column7': shadow lantern copper wheel breeze, 'column8': island violin anchor desert bloom, 'column9': thund │
│ er maple ribbon castle spark, 'column10': falcon mirror ladder pepper frost, 'column11': compass dragon velvet harbor arrow, 'co │
│ lumn12': meadow trumpet coral engine blossom, 'column13': glacier pillow raven sketch amber, 'column14': beacon plume cedar tunn │
│ el oyster, 'column15': summit parrot mosaic ember walnut, 'column16': canyon dolphin quartz needle clover, 'column17': lantern p │
│ ebble falcon orbit willow, 'column18': prism scarlet anchor marble dune, 'column19': temple cobalt raven timber flint, 'column20 │
│ ': atlas crimson hollow spruce pearl}                                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {'column1': apple river cloud hammer bright, 'column2': forest table ocean pencil green, 'column3': window marble stone quick si │
│ lver, 'column4': garden bridge sunset flame candle, 'column5': rocket feather puzzle train bottle, 'column6': mountain crystal t │
│ iger basket lemon, 'column7': shadow lantern copper wheel breeze, 'column8': island violin anchor desert bloom, 'column9': thund │
│ er maple ribbon castle spark, 'column10': falcon mirror ladder pepper frost, 'column11': compass dragon velvet harbor arrow, 'co │
│ lumn12': meadow trumpet coral engine blossom, 'column13': glacier pillow raven sketch amber, 'column14': beacon plume cedar tunn │
│ el oyster, 'column15': summit parrot mosaic ember walnut, 'column16': canyon dolphin quartz needle clover, 'column17': lantern p │
│ ebble falcon orbit willow, 'column18': prism scarlet anchor marble dune, 'column19': temple cobalt raven timber flint, 'column20 │
│ ': atlas crimson hollow spruce pearl}                                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {'column1': apple river cloud hammer bright, 'column2': forest table ocean pencil green, 'column3': window marble stone quick si │
│ lver, 'column4': garden bridge sunset flame candle, 'column5': rocket feather puzzle train bottle, 'column6': mountain crystal t │
│ iger basket lemon, 'column7': shadow lantern copper wheel breeze, 'column8': island violin anchor desert bloom, 'column9': thund │
│ er maple ribbon castle spark, 'column10': falcon mirror ladder pepper frost, 'column11': compass dragon velvet harbor arrow, 'co │
│ lumn12': meadow trumpet coral engine blossom, 'column13': glacier pillow raven sketch amber, 'column14': beacon plume cedar tunn │
│ el oyster, 'column15': summit parrot mosaic ember walnut, 'column16': canyon dolphin quartz needle clover, 'column17': lantern p │
│ ebble falcon orbit willow, 'column18': prism scarlet anchor marble dune, 'column19': temple cobalt raven timber flint, 'column20 │
│ ': atlas crimson hollow spruce pearl}                                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {'column1': apple river cloud hammer bright, 'column2': forest table ocean pencil green, 'column3': window marble stone quick si │
│ lver, 'column4': garden bridge sunset flame candle, 'column5': rocket feather puzzle train bottle, 'column6': mountain crystal t │
│ iger basket lemon, 'column7': shadow lantern copper wheel breeze, 'column8': island violin anchor desert bloom, 'column9': thund │
│ er maple ribbon castle spark, 'column10': falcon mirror ladder pepper frost, 'column11': compass dragon velvet harbor arrow, 'co │
│ lumn12': meadow trumpet coral engine blossom, 'column13': glacier pillow raven sketch amber, 'column14': beacon plume cedar tunn │
│ el oyster, 'column15': summit parrot mosaic ember walnut, 'column16': canyon dolphin quartz needle clover, 'column17': lantern p │
│ ebble falcon orbit willow, 'column18': prism scarlet anchor marble dune, 'column19': temple cobalt raven timber flint, 'column20 │
│ ': atlas crimson hollow spruce pearl}                                                                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ {'column1': apple river cloud hammer bright, 'column2': forest table ocean pencil green, 'column3': window marble stone quick si │
│ lver, 'column4': garden bridge sunset flame candle, 'column5': rocket feather puzzle train bottle, 'column6': mountain crystal t │
│ iger basket lemon, 'column7': shadow lantern copper wheel breeze, 'column8': island violin anchor desert bloom, 'column9': thund │
│ er maple ribbon castle spark, 'column10': falcon mirror ladder pepper frost, 'column11': compass dragon velvet harbor arrow, 'co │
│ lumn12': meadow trumpet coral engine blossom, 'column13': glacier pillow raven sketch amber, 'column14': beacon plume cedar tunn │
│ el oyster, 'column15': summit parrot mosaic ember walnut, 'column16': canyon dolphin quartz needle clover, 'column17': lantern p │
│ ebble falcon orbit willow, 'column18': prism scarlet anchor marble dune, 'column19': temple cobalt raven timber flint, 'column20 │
│ ': atlas crimson hollow spruce pearl}                                                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

i.e. the values correctly show spaces.

### OS:

Linux (Ubuntu 24.04.4 LTS), x86_64

### DuckDB Version:

v1.5.0 (Variegata) 3a3967aa81

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Tomáš Linhart

### Affiliation:

–

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @tlinhart, thanks! I could reproduce the issue.

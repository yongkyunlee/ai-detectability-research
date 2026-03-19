# A DuckDB-based metabase alternative

**HN** | Points: 179 | Comments: 40 | Date: 2026-02-18
**Author:** wowi42
**HN URL:** https://news.ycombinator.com/item?id=47057879
**Link:** https://github.com/taleshape-com/shaper

## Top Comments

**written-beyond:**
This is really nice, specially the pdf report generation.I feel very moronic making a dashboard for any products now. Enterprise customers prefer you integrate into their ERPs anyway.I think we lost the plot as an industry, I've always advocated for having a read only database connection to be available for your customers to make their own visualisations. This should've been the standard 10 years ago and it's case is only stronger in this age of LLMs.We get so involved with our products we forget that our customers are humans too. Nobody wants another account to manage or remember. Analytics and alerts should be push based, configurable reports should get auto generated and sent to your inbox, alerts should be pushed via notifications or emails and customers should have an option to build their own dashboard with something like this.Sane defaults make sense but location matters just as much.

**andrewstuart:**
I wanted to love DuckDB but it was so crashy I had to give up.

**pdyc:**
interesting i am trying to build one too but rejected duckdb because of large size, i guess i will have to give in and use it at some point of time.

**piterrro:**
In what extent this is a metabase alternative? I'm a heavy Metabase user and there's nothing to compare really in this product.

**frafra:**
Metabase works great with DuckDB as well, thanks to 
metabase_duckdb_driver by MotherDuck.

**3abiton:**
As someone who used duckdb but not shaper, what is shaper used for? The readme is scarce on details.

**kavalg:**
This is so cool and also MPL licensed! Thanks!

**ldnbln:**
my company integrated tale shape as our customer-facing metabase dashboard alternative. absolutely love its simplicity!

**thanhnguyen2187:**
Thanks for the cool tool! I think it's worth mentioning SQLPage, which is another tool in similar vein, to generate UI from SQL. From my POV:- SQLPage: more on UI building; doesn't use DuckDB- Shaper: more on analytics&#x2F;dashboard focused with PDF generation and stuff; uses DuckDBhttps:&#x2F;&#x2F;github.com&#x2F;sqlpage&#x2F;SQLPage

**rorylaitila:**
Nice work! I met Jorin a couple years ago at a tech meetup and this was just an idea at the time. So cool to see the consistent progress and updates and to see this come across HN.

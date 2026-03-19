# Show HN: First party analytics pipeline on Cloudflare with DuckDB

**HN** | Points: 3 | Comments: 1 | Date: 2026-01-19
**Author:** cliftonc
**HN URL:** https://news.ycombinator.com/item?id=46677988
**Link:** https://try.icelight.dev/

I spent some time this week wiring together all the pieces to build a "complete" end to end product analytics platform using the new (in beta - use at your own risk) Cloudflare Data Platform, and DuckDB (as I have been wanting to experiment with it for some time).It works surprisingly well!  You can deploy it with one command once you are logged into Wrangler, and it should work on a free Cloudflare account (not sure about this tbh).  The speed is of course what it is given it is running across Iceberg on R2, but it should scale very well at minimal cost.  Would love to hear any feedback &#x2F; ideas etc. but I intend to use this for my own projects as it means I can have a fully owned first party data stack for product analytics.

## Top Comments

**felicitym:**
Thanks for sharing this Clifton. It was really interesting to read more about Icelight (and Drizzle Cube) on your website as well. Sounds like a powerful solution that could be relevant to lots of different contexts. Can't believe you were able to put this together for free! 
https:&#x2F;&#x2F;cliftonc.nl&#x2F;blog&#x2F;icelight-product-analytics-on-cloud...

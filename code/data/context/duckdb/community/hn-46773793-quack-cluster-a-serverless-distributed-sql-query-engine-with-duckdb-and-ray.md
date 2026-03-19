# Quack-Cluster: A Serverless Distributed SQL Query Engine with DuckDB and Ray

**HN** | Points: 80 | Comments: 15 | Date: 2026-01-27
**Author:** tanelpoder
**HN URL:** https://news.ycombinator.com/item?id=46773793
**Link:** https://github.com/kristianaryanto/Quack-Cluster

## Top Comments

**dogman123:**
neat. i'm pretty novice in the guts of this kind of stuff, but how does this work under the hood for blocking operators where they "cannot output a single row until the last row of their input has been seen"?i think this is where spark shuffling comes in? but how does it work here.https:&#x2F;&#x2F;duckdb.org&#x2F;docs&#x2F;stable&#x2F;guides&#x2F;performance&#x2F;how_to_tun...

**mgaunard:**
In my experience ray clusters don't scale well and end up costing you more money. You need to run permanent per-user instances etc.What you need is a multi-tenancy shared infrastructure that is elastic.

**nevalainen:**
feels like a missed opportunity to call it cluster-quack xD

**fodkodrasz:**
So DuckDB was developed to allow queries for bigish data finally without the need for a cluster to simplify data analysis... and we now put it to a cluster?I think there are solutions for that scale of data already, and simplicity is the best feature of DuckDB (at lest for me).

**rfonseca:**
What is the lifetime of the Ray workers, or, in other words, what is the scalability &#x2F; scale-to-zero story that makes this serverless?

**thenaturalist:**
> "Forget about managing complex server infrastructure for your database needs."So what does this run on then?No docs, it's not possible to find any deployment guides for Ray using serverless solutions like Lambda, Cloud Functions or be it your own Firecracker.Instead, every other post mentions EKS or EC2.The Ray team even rejected Lambda support expressedly as far back as 2020 [0]. Uuuuuugh.No thanks! shiverI'd rather cut complexity for practically the same benefit and either do it single machine or have a thin, manageable layer on top a truly serverless infra like in this talk [1] " Processing Trillions of Records at Okta with Mini Serverless Databases".0: https:&#x2F;&#x2F;github.com&#x2F;ray-project&#x2F;ray&#x2F;issues&#x2F;99831: https:&#x2F;&#x2F;www.youtube.com&#x2F;watch?v=TrmJilG4GXk

**pickleballcourt:**
Reminds me of smallpond from deepseek

**hexo:**
Serverless? So it runs on... nothing?

**whattheheckheck:**
Why is everyone so scared of pyspark? Make it run in a local docker image and call it off to a sagemaker processing job

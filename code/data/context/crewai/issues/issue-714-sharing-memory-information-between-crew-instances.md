# Sharing Memory Information Between Crew Instances

**Issue #714** | State: closed | Created: 2024-05-30 | Updated: 2026-03-11
**Author:** ItouTerukazu

In a situation like this:
```
crew1_crew = crew(agent=[agent1, agent2, agent3], 
                   task=[task1, task2, task3], memory=True)

#####################
# etc logic
#####################

crew2_crew = crew(agent=[agent4, agent5, agent6],
                   task=[task4, task5, task6], memory=True)
```

Is it possible to pass memory from crew1_crew to crew2_crew?

Ideally, it would be best if one crew could handle all tasks at once. However, after executing crew1_crew, various processes need to be performed to determine the agent and task of crew2_crew, and the agent and task of crew2_crew will change dynamically.

We would like to share memory (long, short, entity) as part of the same context.
Could you please advise us on the best way to achieve this?

```
crew1_crew = crew(agent=[agent1, agent2, agent3],
                  task=[task1, task2, task3], memory=True)
crew1_crew.kickoff

##################
# etc logic
##################

crew1_crew.agents=[agent4, agent5, agent6]
crew1_crew.tasks=[task4, task5, task6]
crew1_crew.kickoff
```
It would be great if I could reassign the agents and tasks for the crew1_crew instance and execute the kickoff again. However, doing so also results in an error.
If there are any good solutions or workarounds, could you kindly provide guidance on how to proceed?

## Comments

**gadgethome:**
Training your agents with improved memory and allowing them to work on different crews, is something we are looking into. Nothing confirmed yet.

**ItouTerukazu:**
Thank you for your response.

```
crew1_crew = crew(agent=[agent1, agent2, agent3],
                  task=[task1, task2, task3], memory=True)
crew1_crew.kickoff

##################
# etc logic
##################

crew1_crew.agents=[agent4, agent5, agent6] # crew1_crew.agent update
crew1_crew.tasks=[task4, task5, task6]     # crew1_crew.task update
crew1_crew.kickoff
```

I appreciate your response.
Regarding the following steps:

Set agents and tasks for crew1_crew
Execute crew1_crew.kickoff
Add or modify agents and tasks of crew1_crew
Execute crew1_crew.kickoff again

Is it possible to implement this using a different coding approach?
I thought that since the crew1_crew instance remains the same, the memory would also be carried over. What are your thoughts on this?

**anispy211:**
Hey @ItouTerukazu  and others => we've built SuperBrain SDK specifically to solve cross-crew / cross-instance memory sharing in frameworks like CrewAI. It provides a distributed, low-latency shared memory fabric (sub-ms queries, ~5 ms state handoff) that can persist long/short/entity memory externally and make it available across separate crews or dynamic reconfigurations.

Repo: https://github.com/anispy211/superbrainSdk

Demo: https://www.youtube.com/watch?v=TzNxpk5PSXM

Happy to discuss integration (e.g., custom memory provider for CrewAI) — reach out at cto@golightstep.com

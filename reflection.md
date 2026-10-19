# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

To organize a user's schedule around pet care these are the classes required:
- User: The owner responsible of the pet care
- Pet: The animal 
- Task: A designed activity needed to complete to fulfill the needs of the pet (i.e. walks, grooming, feeding)
- Scheduler: A daily plan by listing tasks by priority and fitting them into the owner's available time.

Core actions a user should be able to perform:
1. Set up their owner and pet profile
2. Add and edit pet care tasks
3. Generate and view today's care plan

**b. Design changes**

Yes. After reviewing the class skeleton with AI, I found some missing relationships and logic bottlenecks, and I changed the design before implementing the scheduling logic.

Missing relationships:
- **Scheduler and Pet:** The Scheduler originally took one owner and one pet, but an owner can have several pets and only one daily time budget. Scheduling each pet separately would let every pet use the owner's full available time. I changed the Scheduler to take the Owner and gather tasks from all of the owner's pets, so the time is shared across them.
- **Task and Pet:** A task didn't know which pet it belonged to. Once tasks from several pets are combined into one plan, the plan would show "Walk" without saying whose walk it is. I linked each task to its pet (a `pet_name` field) so the plan stays clear.

Logic bottlenecks:
- **Priority sorting:** Priority was stored as text ("high", "medium", "low"), and sorting text alphabetically puts "low" before "medium". I mapped priorities to numbers so they sort in the right order.
- **Removing tasks:** Two tasks with the same details count as equal, so removing one could delete the wrong task. I gave each task a unique id and changed removal to use it.
- **Completed tasks never reset:** A task marked complete stayed complete forever, which doesn't work for daily care like feeding. I added a frequency (daily or weekly) and changed completion to be tracked by date.
- **Scheduler call order:** `explain_plan()` only works after `generate_plan()`, and running `generate_plan()` twice could duplicate tasks. I made the scheduler clear its previous plan each time it generates a new one.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

**Constraints:** the owner's available time (shared by all pets), task priority, whether a task is due, exact times (like meds at 08:00), and time-of-day preference (morning, afternoon, evening).

**What matters most:** I ranked them by what happens to the pet if one is broken. Time comes first because the owner can't do more than they have time for. Priority decides what gets dropped, since missing meds is worse than missing playtime. Exact times come next, and time-of-day preference matters least because it only changes the order of tasks, not which ones get done.

**b. Tradeoffs**

**Tradeoff: when two fixed-time tasks overlap, the scheduler warns instead of fixing it.** For example, if Luna's meds and Mochi's supplement are both set for 08:00, the plan keeps both at 08:00 and shows a conflict warning. It doesn't move either one.

**Why it's reasonable:** a fixed time is usually set on purpose, like medication. Moving it automatically could make a dose late without the owner noticing, and often the owner can do both at once anyway. A warning lets the owner decide. The downside is that the plan can still contain an overlap the owner has to resolve themselves.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code at every stage of the project:
- **Design brainstorming:** turning the scenario into core user actions, deciding whether Schedule should be its own class (AI suggested a Scheduler class to hold the planning logic), and listing each class's attributes and methods.
- **Diagramming and scaffolding:** generating the Mermaid UML and the dataclass skeletons in `pawpal_system.py`.
- **Design review:** asking it to review the skeleton for missing relationships and logic bottlenecks before writing any logic.
- **Implementation and testing:** filling in the methods, writing `main.py` to try the schedule in the terminal, and drafting pytest tests.

The most helpful prompts were review questions, like "do you notice any missing relationships or potential logic bottlenecks?", asked on code that already existed. They found real problems (priorities sorting alphabetically, one scheduler per pet splitting the owner's time) before they turned into bugs.

**b. Judgment and verification**

I didn't take the AI's suggestions all at once:
- **Picking from the design review:** The review listed nine issues. I chose the two missing relationships (Scheduler and Pet, Task and Pet) and four logic bottlenecks (priority sorting, removing tasks, completion reset, scheduler call order) to fix first.
- **Owner preferences:** When the AI pointed out that `Owner.preferences` was stored but never used, I decided to remove it instead of building a preference feature, because each task's preferred time of day already covered it.
- **Order of work:** When the AI offered to remove preferences, update the UML, and write tests together, I only approved the first two so I could add tests as a separate step.

To verify the results, I ran a two-pet example and read the printed schedule. It caught a real bug: the first version packed every task back to back from 08:00, so the "Evening walk" was scheduled at 08:15. The scheduler was changed so afternoon tasks start at 12:00 or later and evening tasks at 18:00 or later, and I re-ran the example to confirm. I also ran `main.py` and the pytest tests (`python -m pytest`), which pass.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

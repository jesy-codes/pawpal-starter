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

Yes. After reviewing the class skeleton with AI, I found some missing relationships and logic bottlenecks to fix before implementing the scheduling logic.

Missing relationships:
- **Scheduler and Pet:** The Scheduler originally took one owner and one pet, but an owner can have several pets and only one daily time budget. Scheduling each pet separately would let every pet use the owner's full available time. I'm changing the Scheduler to take the Owner and gather tasks from all of the owner's pets, so the time is shared across them.
- **Task and Pet:** A task didn't know which pet it belonged to. Once tasks from several pets are combined into one plan, the plan would show "Walk" without saying whose walk it is. I'm linking each task to its pet so the plan stays clear.

Logic bottlenecks:
- **Priority sorting:** Priority was stored as text ("high", "medium", "low"), and sorting text alphabetically puts "low" before "medium". I'm mapping priorities to numbers so they sort in the right order.
- **Removing tasks:** Two tasks with the same details count as equal, so removing one could delete the wrong task. Giving each task a unique id fixes this.
- **Completed tasks never reset:** A task marked complete stayed complete forever, which doesn't work for daily care like feeding. Tasks need a frequency (daily or weekly) and completion tracked by date.
- **Scheduler call order:** `explain_plan()` only works after `generate_plan()`, and running `generate_plan()` twice could duplicate tasks. The scheduler should clear its previous plan each time it generates a new one.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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

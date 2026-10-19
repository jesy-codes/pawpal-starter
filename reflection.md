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

Yes. When I had AI review my skeleton, it found a few things I'd missed, so I fixed them before writing any real logic:

- The Scheduler took one owner and one pet. But an owner can have a few pets and only one day, so each pet would've gotten the full time. Now the Scheduler takes the Owner and pulls tasks from all the pets.
- Tasks didn't know which pet they belonged to, so a combined plan would just say "Walk" without saying whose walk. I added a `pet_name`.
- Priority was text, and sorting text alphabetically puts "low" before "medium". I switched to numbers.
- Two identical tasks counted as equal, so removing one could remove the wrong one. Every task gets an id now.
- A completed task stayed completed forever, which doesn't work for feeding every day. I added daily/weekly and track completion by date.
- Running `generate_plan()` twice could duplicate tasks, so it clears the old plan first.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler looks at the owner's available time (shared by all pets), priority, whether a task is due, exact times like meds at 08:00, and morning/afternoon/evening preferences.

I ranked them by what happens to the pet if one gets broken. Time comes first since you can't do more than you have time for. Priority decides what gets cut, because missing meds is worse than missing playtime. Exact times come next, and time of day matters least since it only changes the order, not what gets done.

**b. Tradeoffs**

If two fixed-time tasks overlap (like Luna's meds and Mochi's supplement both at 08:00), the scheduler warns me instead of moving one. I think that's fine because fixed times are usually on purpose, like medication, and quietly pushing a dose later seems worse than just telling the owner. The downside is the owner has to sort it out themselves.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code for pretty much every step: brainstorming the classes, making the UML and the skeleton, reviewing the design, writing the logic, the tests, and hooking up the Streamlit app. The most useful prompts were the review ones, like "do you see any missing relationships or bottlenecks?" on code I already had. That's how I caught the priority sorting and the one-pet scheduler problems early.

**b. Judgment and verification**

I didn't just take everything it said. The review listed nine issues and I picked six to fix. It also pointed out that `Owner.preferences` wasn't used anywhere, and instead of building a whole feature for it I just deleted it, since tasks already have a preferred time of day. And when it offered to do three things at once, I said yes to two and kept tests as their own step.

To check things, I ran the code and read the output. The first two-pet run had the evening walk at 08:15, which was obviously wrong, so we fixed it so afternoon tasks start at 12:00 and evening ones at 18:00.

**c. AI strategy**

What helped most was having it actually run stuff (`main.py`, the tests, a fake click-through of the app, even rendering the UML) instead of just writing code. That caught real problems: the 08:15 evening walk, plans after midnight sorting wrong, UML notes showing `\n` as text, and a README example that said 65 minutes when the app said 70.

One suggestion I changed: the review suggested a `ScheduledTask` class to hold each task's start time and reason. I skipped it at first and used two dictionaries. Once I added fixed times, sorting, and conflicts, that got messy, so I added `ScheduledTask` then. I liked adding it when I actually needed it instead of up front.

Using separate chats for different phases kept each one focused on one thing. A new chat only knows what's in the files, so if the code and the README didn't match anymore, it showed up fast.

The big thing I learned about being the "lead architect" is that the AI is really fast, but it doesn't decide what matters. I still had to pick which issues to fix, decide that conflicts should warn instead of moving meds around, and keep the design small. And I learned not to trust "done" until I'd seen it run.

---

## 4. Testing and Verification

**a. What you tested**

There are 21 tests. They cover sorting (including past midnight), picking tasks by priority when time is short, daily and weekly repeats (even Oct 31 → Nov 1 and Dec 28 → Jan 4), conflicts (including two pets at the exact same time, and back-to-back tasks not counting), filtering, and bad input like "25:00". These are the rules an owner actually depends on. If recurrence breaks, a pet could miss a feeding and nothing would tell you.

**b. Confidence**

4 out of 5. Everything passes, and testing found a real bug (plans past midnight were in the wrong order) that was fixed. It's not a 5 because the Streamlit app doesn't have automated tests, and picking by priority can leave some time unused.

---

## 5. Reflection

**a. What went well**
The algorithm and trade-off reflection help me design better this app. 

**b. What you would improve**
Maybe save data between sessions (right now it's gone when the app restarts), and have conflicts suggest a free time instead of just warning.

**c. Key takeaway**
Doing the design first was worth it. The biggest problems got caught in the UML and skeleton before there was any real logic to fix. After that, running things and testing was the only way I really knew whether something worked.

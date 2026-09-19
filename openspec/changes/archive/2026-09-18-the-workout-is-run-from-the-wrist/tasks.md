## 1. The outer test

- [x] 1.1 Write the browser-tier test where a set is logged, the fitness field's notice is written as the watch writes it, and the workout lands in the field as a document without the page being touched, marked `test.fail()`.

## 2. Following the notice

- [x] 2.1 Write a browser-tier test that a notice saying a workout runs, taken after the page's workout began, makes the page show the time running from it.
- [x] 2.2 Write a browser-tier test that a notice taken before the page's workout began leaves the workout's start alone.
- [x] 2.3 Write a browser-tier test that a field whose notice nobody wrote leaves the trainer working exactly as it does now.
- [x] 2.4 Write a browser-tier test that a notice route answering nothing at all leaves the trainer working.

## 3. Saved from the wrist

- [x] 3.1 Write a browser-tier test that a notice saying the workout is finished uploads it and starts a fresh workout, the page saying the watch ended it.
- [x] 3.2 Write a browser-tier test that the same notice read again saves nothing further.
- [x] 3.3 Write a browser-tier test that a finish notice with no set logged uploads nothing and says so.
- [x] 3.4 Write a browser-tier test that a finish notice whose upload fails still says the workout was not saved and keeps its text reachable.

## 4. What the page reaches

- [x] 4.1 Write a test that the trainer's addresses are still only cora's own and the hosts the suite names, the notice among them.
- [x] 4.2 Write a test that the page holds no heart line and asks for no pulse.

## 5. What the watch writes

- [x] 5.1 Write a test that the plugin ships the extension's source outside the packaged module, so no wheel carries it.
- [x] 5.2 Write a test that the extension writes the field's notice when its screen is created.
- [x] 5.3 Write a test that the extension binds a click that writes the finish, and writes nothing else.
- [x] 5.4 Write a test that the extension asks for no sensor permission.
- [x] 5.5 Write a test that the extension's address is read from what the build writes, never hard-coded.

## 6. Building it

- [x] 6.1 Write a test that the build writes the extension's address from the machine's own name, and from the override when one is given.
- [x] 6.2 Write a test that a build with no Zepp tooling on the path stops and names the command that installs it.

## 7. Close it

- [x] 7.1 Drop the outer test's `test.fail()` marker and watch it pass.

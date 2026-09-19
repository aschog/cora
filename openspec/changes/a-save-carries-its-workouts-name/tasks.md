## 1. The outer test

- [x] 1.1 Write the functional test where a titled save and an untitled one list as one day naming the workout and the untitled save's exercise, and in detail with the name on the day's line, marked `@pytest.mark.xfail(strict=True)`.

## 2. The grammar takes a name

- [x] 2.1 Write a test that one line before the first heading is the session's name.
- [x] 2.2 Write a test that a second line before the first heading refuses the document by line.

## 3. The listing names the workout

- [x] 3.1 Write a test that a day names its workouts each once, and an untitled save's exercises in their place.
- [x] 3.2 Write a test that in detail the day's line carries its workouts' names after the date.

## 4. The trainer names the save

- [x] 4.1 Write a test that the page reads the workout's name off the CSV's filename header, keeps it with the plan, and writes it first in a save.

## 5. Close it

- [x] 5.1 Drop the outer test's `xfail` marker and watch it pass.
